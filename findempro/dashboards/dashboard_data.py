dashboard_data = [
    {
        "title": "Demand Analysis",
        "chart_type": "line",
        "chart_data": {
            "series": [{
                "name": "Demanda",
                "data": [12, 19, 3, 5, 2],
                "borderColor": "rgba(75, 192, 192, 1)",
                "borderWidth": 2
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
                    {"x": "2023-01-01", "y": [60, 80, 50, 70]},
                    {"x": "2023-02-01", "y": [70, 90, 60, 80]},
                    {"x": "2023-03-01", "y": [80, 100, 70, 90]}
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
