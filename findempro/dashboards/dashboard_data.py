chart_data = [
    {
        "title": "Demand Analysis",
        "chart_type": "line",
        "chart_data": {
            "series": [{
                "x": 1, "y": 12
            }, {
                "x": 2, "y": 19
            }, {
                "x": 3, "y": 3
            }, {
                "x": 4, "y": 5
            }, {
                "x": 5, "y": 2
            }],
            "options": {
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        },
        "widget_config": {"key1": "value1", "key2": "value2"},
        "layout_config": {"key3": "value3", "key4": "value4"}
    },
    {
        "title": "Demand Simulation",
        "chart_type": "candlestick",
        "chart_data": {
            "series": [{
                "data": [
                    {"x": 1641062400000, "y": [60, 80, 50, 70]},  # 2023-01-01
                    {"x": 1643740800000, "y": [70, 90, 60, 80]},  # 2023-02-01
                    {"x": 1646160000000, "y": [80, 100, 70, 90]}  # 2023-03-01
                ]
            }],
            "options": {
                "chart": {"type": "candlestick", "height": 350},
                "xaxis": {"type": "datetime"},
                "title": {"text": "Candlestick Chart"}
            }
        },
        "widget_config": {"key5": "value5", "key6": "value6"},
        "layout_config": {"key7": "value7", "key8": "value8"}
    },
    {
        "title": "Cost Breakdown",
        "chart_type": "line",
        "chart_data": {
            "series": [{
                "name": "Profit",
                "type": "column",
                "data": [10, 15, 5, 20, 12],
            }, {
                "name": "Loss",
                "type": "line",
                "data": [5, 10, 2, 12, 8],
            }],
            "options": {
                "chart": {"height": 350, "type": "line"},
                "xaxis": {"categories": ['Jan', 'Feb', 'Mar', 'Apr', 'May']}
            }
        },
        "widget_config": {"key9": "value9", "key10": "value10"},
        "layout_config": {"key11": "value11", "key12": "value12"}
    },
]
