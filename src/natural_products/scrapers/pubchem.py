"""
PubChem API Client — Fetch compound data for natural products.
PubChem is the world's largest free chemical database (NIH).
API docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class PubChemClient:
    """Async client for PubChem PUG REST API."""

    def __init__(self, rate_limit_per_second: int = 5):
        self._last_call = 0.0
        self._min_interval = 1.0 / rate_limit_per_second
        self._client = httpx.AsyncClient(timeout=30.0)

    async def _get(self, url: str, params: Optional[dict] = None) -> dict | list | None:
        """Rate-limited GET with retry."""
        now = time.time()
        wait = self._min_interval - (now - self._last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call = time.time()

        for attempt in range(3):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    return None
                elif resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.warning(f"PubChem returned {resp.status_code} for {url}")
                    return None
            except Exception as e:
                logger.warning(f"PubChem request failed (attempt {attempt+1}): {e}")
                await asyncio.sleep(1.0)
        return None

    async def get_cid_by_name(self, name: str) -> Optional[int]:
        """Get PubChem CID by compound name."""
        url = f"{PUBCHEM_BASE}/compound/name/{httpx.URL(name).path}/cids/JSON"
        result = await self._get(url)
        if result and "IdentifierList" in result:
            cids = result["IdentifierList"].get("CID", [])
            return cids[0] if cids else None
        return None

    async def get_properties(self, cid: int) -> Optional[dict]:
        """Get key physicochemical properties for a CID."""
        props = [
            "MolecularFormula",
            "MolecularWeight",
            "XLogP",
            "HBondDonorCount",
            "HBondAcceptorCount",
            "RotatableBondCount",
            "TPSA",
            "Complexity",
            "HeavyAtomCount",
            "IsomericSMILES",
            "IUPACName",
            "InChIKey",
        ]
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{','.join(props)}/JSON"
        result = await self._get(url)
        if result and "PropertyTable" in result:
            props_list = result["PropertyTable"].get("Properties", [])
            return props_list[0] if props_list else None
        return None

    async def get_bioactivity(self, cid: int, limit: int = 100) -> list[dict]:
        """Get known biological activities (targets) for a compound."""
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/assaysummary/JSON"
        result = await self._get(url)
        if result and "Table" in result:
            rows = result["Table"].get("Row", [])
            return rows[:limit]
        return []

    async def fetch_compound(self, name: str) -> Optional[dict]:
        """
        Full compound data fetch by name.
        Returns structured dict with all relevant properties.
        """
        logger.info(f"Fetching PubChem data for: {name}")

        cid = await self.get_cid_by_name(name)
        if not cid:
            logger.warning(f"CID not found for: {name}")
            return None

        props = await self.get_properties(cid)
        if not props:
            return None

        # Check Lipinski's Rule of Five (drug-likeness)
        mw = float(props.get("MolecularWeight", 0))
        logp = float(props.get("XLogP", 0))
        hbd = int(props.get("HBondDonorCount", 0))
        hba = int(props.get("HBondAcceptorCount", 0))
        tpsa = float(props.get("TPSA", 0))

        lipinski_pass = (mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10)
        bioavailability_flag = (
            lipinski_pass and tpsa < 140 and int(props.get("RotatableBondCount", 0)) <= 10
        )

        return {
            "name": name,
            "cid": cid,
            "molecular_formula": props.get("MolecularFormula"),
            "molecular_weight": mw,
            "logP": logp,
            "hbd": hbd,
            "hba": hba,
            "tpsa": tpsa,
            "rotatable_bonds": int(props.get("RotatableBondCount", 0)),
            "smiles": props.get("IsomericSMILES"),
            "iupac_name": props.get("IUPACName"),
            "inchikey": props.get("InChIKey"),
            "lipinski_pass": lipinski_pass,
            "oral_bioavailability_predicted": bioavailability_flag,
            "source": "PubChem",
        }

    async def close(self):
        await self._client.aclose()


class ChEMBLClient:
    """Client for ChEMBL bioactivity data."""

    BASE = "https://www.ebi.ac.uk/chembl/api/data"

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"})

    async def get_targets_for_compound(
        self, chembl_id: str = None, smiles: str = None, limit: int = 20
    ) -> list[dict]:
        """Get known protein targets for a compound."""
        if chembl_id:
            url = f"{self.BASE}/activity.json?molecule_chembl_id={chembl_id}&limit={limit}"
        elif smiles:
            # Search by SMILES similarity
            url = f"{self.BASE}/similarity/{httpx.URL(smiles).path}/85.json?limit={limit}"
        else:
            return []

        try:
            resp = await self._client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("activities", [])
        except Exception as e:
            logger.warning(f"ChEMBL request failed: {e}")
        return []

    async def close(self):
        await self._client.aclose()
