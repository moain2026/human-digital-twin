"""
Unit tests for Natural Products Database.
"""
import pytest
from src.natural_products.database.compound_db import NaturalProductsDB


class TestNaturalProductsDB:
    def setup_method(self):
        self.db = NaturalProductsDB()

    def test_builtin_compounds_loaded(self):
        compounds = self.db.get_all()
        assert len(compounds) >= 5

    def test_get_by_name_exact(self):
        c = self.db.get("Curcumin")
        assert c is not None
        assert c["name"] == "Curcumin"

    def test_get_case_insensitive(self):
        c = self.db.get("curcumin")
        assert c is not None

    def test_get_nonexistent_returns_none(self):
        c = self.db.get("NonExistentHerb12345")
        assert c is None

    def test_berberine_has_effects(self):
        c = self.db.get("Berberine")
        assert c is not None
        effects = c.get("biomarker_effects", {})
        assert "glucose_fasting" in effects
        assert effects["glucose_fasting"] < 0  # Should lower glucose

    def test_thymoquinone_targets(self):
        c = self.db.get("Thymoquinone")
        assert c is not None
        assert "NF-κB" in c.get("primary_targets", [])

    def test_interaction_check_piperine(self):
        result = self.db.get_interaction_risk(["Curcumin", "Piperine"])
        assert "risk" in result
        assert "details" in result
        assert len(result["details"]) > 0  # Piperine always adds notes

    def test_combined_effect_prediction(self):
        effects = self.db.predict_combined_biomarker_effect(["Thymoquinone", "Berberine"])
        assert isinstance(effects, dict)
        assert len(effects) > 0
        # Both reduce glucose — should have a glucose effect
        assert "glucose_fasting" in effects

    def test_piperine_enhances_effects(self):
        effects_without = self.db.predict_combined_biomarker_effect(["Berberine"])
        effects_with = self.db.predict_combined_biomarker_effect(["Berberine", "Piperine"])
        # Piperine should enhance effects (make them larger in magnitude)
        bm = "glucose_fasting"
        if bm in effects_without and bm in effects_with:
            assert abs(effects_with[bm]) > abs(effects_without[bm])

    def test_search(self):
        results = self.db.search("anti_inflammatory", field="mechanisms")
        assert len(results) > 0

    def test_add_compound(self):
        new = {
            "name": "TestHerb",
            "mechanisms": ["test"],
            "biomarker_effects": {"glucose_fasting": -1.0},
            "interaction_risk": "low",
        }
        self.db.add(new)
        c = self.db.get("TestHerb")
        assert c is not None
        assert c["name"] == "TestHerb"
