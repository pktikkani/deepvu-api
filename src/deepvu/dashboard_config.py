"""Fixed dashboard type → tab definitions with full UI structure.

Each tab includes sub-tabs, filters (dropdowns), charts, and table schemas
so the frontend knows exactly what to render.
"""

from typing import Any

TabConfig = dict[str, Any]

# --- Shared tab definitions (reused across dashboard types) ---

CAMPAIGN_OVERVIEW_TAB: TabConfig = {
    "key": "campaign_overview",
    "label": "Campaign Overview",
    "order": 1,
    "sub_tabs": [
        {"key": "overall", "label": "Overall"},
        {"key": "youtube", "label": "YouTube"},
    ],
    "filters": [],
    "charts": [],
    "tables": [],
}

REACH_FREQUENCY_TAB: TabConfig = {
    "key": "reach_frequency",
    "label": "Reach & Frequency",
    "order": 2,
    "sub_tabs": [],
    "filters": [
        {"key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown"},
        {"key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown"},
    ],
    "charts": [],
    "tables": [],
}

DEVICE_TYPE_TAB: TabConfig = {
    "key": "device_type",
    "label": "Device Type",
    "order": 3,
    "sub_tabs": [],
    "filters": [
        {"key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown"},
        {"key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown"},
    ],
    "charts": [
        {"key": "device_type_spends", "label": "Device Type by Spends", "type": "pie"},
        {"key": "device_type_impressions", "label": "Device Type by Impressions", "type": "pie"},
        {"key": "device_type_clicks", "label": "Device Type by Clicks", "type": "pie"},
        {"key": "device_type_views", "label": "Device Type by Views", "type": "pie"},
    ],
    "tables": [
        {
            "key": "snapshot",
            "label": "Snapshot",
            "columns": [
                {"key": "device_type", "label": "Device Type", "sortable": True},
                {"key": "currency", "label": "Currency", "sortable": True},
                {"key": "spends", "label": "Spends", "sortable": True},
                {"key": "impressions", "label": "Impressions", "sortable": True},
                {"key": "clicks", "label": "Clicks", "sortable": True},
                {"key": "ctr", "label": "CTR", "sortable": True},
                {"key": "views", "label": "Views", "sortable": True},
                {"key": "vtr", "label": "VTR", "sortable": True},
            ],
        }
    ],
}

GEO_TRENDS_TAB: TabConfig = {
    "key": "geo_trends",
    "label": "Geo Trends",
    "order": 4,
    "sub_tabs": [
        {
            "key": "region",
            "label": "Region",
            "charts": [
                {"key": "spends_share", "label": "Spends Share", "type": "pie"},
            ],
            "tables": [
                {
                    "key": "tabular_view",
                    "label": "Tabular View",
                    "layout": "side_by_side_with_chart",
                    "columns": [
                        {"key": "region", "label": "Region", "sortable": True},
                        {"key": "currency", "label": "Currency", "sortable": True},
                        {"key": "spends", "label": "Spends", "sortable": True},
                        {"key": "impressions", "label": "Impressions", "sortable": True},
                        {"key": "cpm", "label": "CPM", "sortable": True},
                    ],
                }
            ],
        },
        {
            "key": "city",
            "label": "City",
            "charts": [
                {"key": "spends_share", "label": "Spends Share", "type": "pie"},
            ],
            "tables": [
                {
                    "key": "tabular_view",
                    "label": "Tabular View",
                    "layout": "side_by_side_with_chart",
                    "columns": [
                        {"key": "city", "label": "City", "sortable": True},
                        {"key": "currency", "label": "Currency", "sortable": True},
                        {"key": "spends", "label": "Spends", "sortable": True},
                        {"key": "impressions", "label": "Impressions", "sortable": True},
                        {"key": "cpm", "label": "CPM", "sortable": True},
                    ],
                }
            ],
        },
    ],
    "filters": [
        {"key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown", "layout": "inline"},
        {"key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown", "layout": "inline"},
    ],
    "charts": [],
    "tables": [],
}

PLACEMENTS_TAB: TabConfig = {
    "key": "placements",
    "label": "Placements",
    "order": 5,
    "sub_tabs": [],
    "filters": [],
    "charts": [],
    "tables": [],
}

CREATIVE_TAB: TabConfig = {
    "key": "creative",
    "label": "Creative",
    "order": 6,
    "sub_tabs": [],
    "filters": [
        {"key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown", "layout": "inline"},
        {"key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown", "layout": "inline"},
        {"key": "format", "label": "Format", "type": "dropdown", "layout": "inline"},
        {"key": "concept", "label": "Concept", "type": "dropdown", "layout": "inline"},
        {"key": "size", "label": "Size", "type": "dropdown", "layout": "inline"},
    ],
    "charts": [],
    "tables": [
        {
            "key": "creative_performance",
            "label": "Creative Performance",
            "columns": [
                {"key": "creative", "label": "Creative", "sortable": True},
                {"key": "creative_name", "label": "Creative Name", "sortable": True},
                {"key": "format", "label": "Format", "sortable": True},
                {"key": "currency", "label": "Currency", "sortable": True},
                {"key": "spends", "label": "Spends", "sortable": True},
                {"key": "impressions", "label": "Impressions", "sortable": True},
                {"key": "cpm", "label": "CPM", "sortable": True},
                {"key": "clicks", "label": "Clicks", "sortable": True},
                {"key": "ctr", "label": "CTR", "sortable": True},
            ],
        }
    ],
}

# --- Dashboard type → tabs mapping ---

DASHBOARD_TABS: dict[str, list[TabConfig]] = {
    "comprehensive": [
        CAMPAIGN_OVERVIEW_TAB,
        REACH_FREQUENCY_TAB,
        DEVICE_TYPE_TAB,
        GEO_TRENDS_TAB,
        PLACEMENTS_TAB,
        CREATIVE_TAB,
    ],
    "limited": [
        {**CAMPAIGN_OVERVIEW_TAB, "order": 1},
        {**GEO_TRENDS_TAB, "order": 2},
        {**PLACEMENTS_TAB, "order": 3},
    ],
}

VALID_DASHBOARD_TYPES = set(DASHBOARD_TABS.keys())


def get_tabs_for_type(dashboard_type: str) -> list[TabConfig]:
    if dashboard_type not in VALID_DASHBOARD_TYPES:
        raise ValueError(f"Invalid dashboard type: {dashboard_type}")
    return DASHBOARD_TABS[dashboard_type]
