import pytest

from deepvu.dashboard_config import DASHBOARD_TABS, get_tabs_for_type


class TestDashboardConfig:
    def test_comprehensive_has_six_tabs(self):
        tabs = get_tabs_for_type("comprehensive")
        assert len(tabs) == 6

    def test_comprehensive_tab_keys(self):
        tabs = get_tabs_for_type("comprehensive")
        keys = [t["key"] for t in tabs]
        assert keys == [
            "campaign_overview",
            "reach_frequency",
            "device_type",
            "geo_trends",
            "placements",
            "creative",
        ]

    def test_limited_has_three_tabs(self):
        tabs = get_tabs_for_type("limited")
        assert len(tabs) == 3

    def test_limited_tab_keys(self):
        tabs = get_tabs_for_type("limited")
        keys = [t["key"] for t in tabs]
        assert keys == ["campaign_overview", "geo_trends", "placements"]

    def test_limited_is_subset_of_comprehensive(self):
        comp_keys = {t["key"] for t in DASHBOARD_TABS["comprehensive"]}
        limited_keys = {t["key"] for t in DASHBOARD_TABS["limited"]}
        assert limited_keys.issubset(comp_keys)

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid dashboard type"):
            get_tabs_for_type("premium")

    def test_all_tabs_have_required_fields(self):
        for dtype, tabs in DASHBOARD_TABS.items():
            for tab in tabs:
                assert "key" in tab, f"{dtype} tab missing 'key'"
                assert "label" in tab, f"{dtype} tab missing 'label'"
                assert "order" in tab, f"{dtype} tab missing 'order'"


class TestCampaignOverviewTab:
    def test_has_sub_tabs(self):
        tabs = get_tabs_for_type("comprehensive")
        co = next(t for t in tabs if t["key"] == "campaign_overview")
        sub_keys = [s["key"] for s in co["sub_tabs"]]
        assert sub_keys == ["overall", "youtube"]


class TestDeviceTypeTab:
    def test_has_filters(self):
        tabs = get_tabs_for_type("comprehensive")
        dt = next(t for t in tabs if t["key"] == "device_type")
        filter_keys = [f["key"] for f in dt["filters"]]
        assert "sub_campaign" in filter_keys
        assert "plan_line_item" in filter_keys

    def test_has_four_pie_charts(self):
        tabs = get_tabs_for_type("comprehensive")
        dt = next(t for t in tabs if t["key"] == "device_type")
        assert len(dt["charts"]) == 4
        assert all(c["type"] == "pie" for c in dt["charts"])

    def test_snapshot_table_columns(self):
        tabs = get_tabs_for_type("comprehensive")
        dt = next(t for t in tabs if t["key"] == "device_type")
        table = dt["tables"][0]
        assert table["key"] == "snapshot"
        col_keys = [c["key"] for c in table["columns"]]
        assert col_keys == [
            "device_type", "currency", "spends", "impressions",
            "clicks", "ctr", "views", "vtr",
        ]

    def test_all_columns_sortable(self):
        tabs = get_tabs_for_type("comprehensive")
        dt = next(t for t in tabs if t["key"] == "device_type")
        for table in dt["tables"]:
            for col in table["columns"]:
                assert col["sortable"] is True


class TestGeoTrendsTab:
    def test_has_region_and_city_sub_tabs(self):
        tabs = get_tabs_for_type("comprehensive")
        geo = next(t for t in tabs if t["key"] == "geo_trends")
        sub_keys = [s["key"] for s in geo["sub_tabs"]]
        assert sub_keys == ["region", "city"]

    def test_region_has_pie_chart_and_table(self):
        tabs = get_tabs_for_type("comprehensive")
        geo = next(t for t in tabs if t["key"] == "geo_trends")
        region = next(s for s in geo["sub_tabs"] if s["key"] == "region")
        assert len(region["charts"]) == 1
        assert region["charts"][0]["type"] == "pie"
        assert len(region["tables"]) == 1
        assert region["tables"][0]["layout"] == "side_by_side_with_chart"

    def test_inline_filters(self):
        tabs = get_tabs_for_type("comprehensive")
        geo = next(t for t in tabs if t["key"] == "geo_trends")
        for f in geo["filters"]:
            assert f["layout"] == "inline"


class TestCreativeTab:
    def test_has_five_filters(self):
        tabs = get_tabs_for_type("comprehensive")
        cr = next(t for t in tabs if t["key"] == "creative")
        filter_keys = [f["key"] for f in cr["filters"]]
        assert filter_keys == [
            "sub_campaign", "plan_line_item", "format", "concept", "size",
        ]

    def test_creative_performance_table(self):
        tabs = get_tabs_for_type("comprehensive")
        cr = next(t for t in tabs if t["key"] == "creative")
        table = cr["tables"][0]
        assert table["key"] == "creative_performance"
        col_keys = [c["key"] for c in table["columns"]]
        assert col_keys == [
            "creative", "creative_name", "format", "currency",
            "spends", "impressions", "cpm", "clicks", "ctr",
        ]

    def test_all_columns_sortable(self):
        tabs = get_tabs_for_type("comprehensive")
        cr = next(t for t in tabs if t["key"] == "creative")
        for table in cr["tables"]:
            for col in table["columns"]:
                assert col["sortable"] is True
