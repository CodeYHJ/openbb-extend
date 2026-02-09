## 这是 api

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Quant Data API",
    "description": "量化数据查询接口 - 仅提供读取功能",
    "version": "1.0.0"
  },
  "paths": {
    "/api/v1/macro/indicators": {
      "get": {
        "tags": ["宏观数据"],
        "summary": "List Indicators",
        "description": "获取所有宏观指标列表",
        "operationId": "list_indicators_api_v1_macro_indicators_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "items": { "$ref": "#/components/schemas/MacroIndicator" },
                  "type": "array",
                  "title": "Response List Indicators Api V1 Macro Indicators Get"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/macro/data": {
      "get": {
        "tags": ["宏观数据"],
        "summary": "Get Macro Data",
        "description": "查询指定宏观指标的历史数据\n\n- series_id: 指标代码，可通过 /indicators 接口查询\n- start_date: 可选，默认不限制\n- end_date: 可选，默认不限制",
        "operationId": "get_macro_data_api_v1_macro_data_get",
        "parameters": [
          {
            "name": "series_id",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "description": "指标代码，如 WALCL",
              "title": "Series Id"
            },
            "description": "指标代码，如 WALCL"
          },
          {
            "name": "start_date",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                { "type": "string", "format": "date" },
                { "type": "null" }
              ],
              "description": "开始日期 (YYYY-MM-DD)",
              "title": "Start Date"
            },
            "description": "开始日期 (YYYY-MM-DD)"
          },
          {
            "name": "end_date",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                { "type": "string", "format": "date" },
                { "type": "null" }
              ],
              "description": "结束日期 (YYYY-MM-DD)",
              "title": "End Date"
            },
            "description": "结束日期 (YYYY-MM-DD)"
          },
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "maximum": 10000,
              "minimum": 1,
              "description": "返回条数限制",
              "default": 1000,
              "title": "Limit"
            },
            "description": "返回条数限制"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/MacroDataItem" },
                  "title": "Response Get Macro Data Api V1 Macro Data Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/HTTPValidationError" }
              }
            }
          }
        }
      }
    },
    "/api/v1/macro/data/latest": {
      "get": {
        "tags": ["宏观数据"],
        "summary": "Get Latest Data",
        "description": "获取指定指标的最新数据",
        "operationId": "get_latest_data_api_v1_macro_data_latest_get",
        "parameters": [
          {
            "name": "series_id",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "description": "指标代码",
              "title": "Series Id"
            },
            "description": "指标代码"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "anyOf": [
                    { "$ref": "#/components/schemas/MacroDataItem" },
                    { "type": "null" }
                  ],
                  "title": "Response Get Latest Data Api V1 Macro Data Latest Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/HTTPValidationError" }
              }
            }
          }
        }
      }
    },
    "/api/v1/stocks/symbols": {
      "get": {
        "tags": ["股票数据"],
        "summary": "List Symbols",
        "description": "获取所有股票代码列表",
        "operationId": "list_symbols_api_v1_stocks_symbols_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "items": { "$ref": "#/components/schemas/StockSymbol" },
                  "type": "array",
                  "title": "Response List Symbols Api V1 Stocks Symbols Get"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/stocks/data": {
      "get": {
        "tags": ["股票数据"],
        "summary": "Get Stock Data",
        "description": "查询指定股票的历史日线数据\n\n- symbol: 股票代码\n- start_date: 可选，默认不限制\n- end_date: 可选，默认不限制",
        "operationId": "get_stock_data_api_v1_stocks_data_get",
        "parameters": [
          {
            "name": "symbol",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "description": "股票代码，如 AAPL",
              "title": "Symbol"
            },
            "description": "股票代码，如 AAPL"
          },
          {
            "name": "start_date",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                { "type": "string", "format": "date" },
                { "type": "null" }
              ],
              "description": "开始日期 (YYYY-MM-DD)",
              "title": "Start Date"
            },
            "description": "开始日期 (YYYY-MM-DD)"
          },
          {
            "name": "end_date",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                { "type": "string", "format": "date" },
                { "type": "null" }
              ],
              "description": "结束日期 (YYYY-MM-DD)",
              "title": "End Date"
            },
            "description": "结束日期 (YYYY-MM-DD)"
          },
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "maximum": 10000,
              "minimum": 1,
              "description": "返回条数限制",
              "default": 1000,
              "title": "Limit"
            },
            "description": "返回条数限制"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/StockDataItem" },
                  "title": "Response Get Stock Data Api V1 Stocks Data Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/HTTPValidationError" }
              }
            }
          }
        }
      }
    },
    "/api/v1/stocks/data/latest": {
      "get": {
        "tags": ["股票数据"],
        "summary": "Get Latest Data",
        "description": "获取指定股票的最新数据",
        "operationId": "get_latest_data_api_v1_stocks_data_latest_get",
        "parameters": [
          {
            "name": "symbol",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "description": "股票代码",
              "title": "Symbol"
            },
            "description": "股票代码"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "anyOf": [
                    { "$ref": "#/components/schemas/StockDataItem" },
                    { "type": "null" }
                  ],
                  "title": "Response Get Latest Data Api V1 Stocks Data Latest Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/HTTPValidationError" }
              }
            }
          }
        }
      }
    },
    "/": {
      "get": {
        "summary": "Root",
        "description": "根路径重定向到文档",
        "operationId": "root__get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": { "application/json": { "schema": {} } }
          }
        }
      }
    },
    "/api/v1/health": {
      "get": {
        "summary": "Health Check",
        "description": "健康检查端点",
        "operationId": "health_check_api_v1_health_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": { "application/json": { "schema": {} } }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": { "$ref": "#/components/schemas/ValidationError" },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "MacroDataItem": {
        "properties": {
          "date": { "type": "string", "format": "date", "title": "Date" },
          "series_id": { "type": "string", "title": "Series Id" },
          "indicator_name": {
            "anyOf": [{ "type": "string" }, { "type": "null" }],
            "title": "Indicator Name"
          },
          "value": { "type": "number", "title": "Value" },
          "frequency": {
            "anyOf": [{ "type": "string" }, { "type": "null" }],
            "title": "Frequency"
          },
          "provider": { "type": "string", "title": "Provider" }
        },
        "type": "object",
        "required": [
          "date",
          "series_id",
          "indicator_name",
          "value",
          "frequency",
          "provider"
        ],
        "title": "MacroDataItem"
      },
      "MacroIndicator": {
        "properties": {
          "series_id": { "type": "string", "title": "Series Id" },
          "indicator_name": { "type": "string", "title": "Indicator Name" },
          "frequency": { "type": "string", "title": "Frequency" }
        },
        "type": "object",
        "required": ["series_id", "indicator_name", "frequency"],
        "title": "MacroIndicator"
      },
      "StockDataItem": {
        "properties": {
          "date": { "type": "string", "format": "date", "title": "Date" },
          "symbol": { "type": "string", "title": "Symbol" },
          "open": {
            "anyOf": [{ "type": "number" }, { "type": "null" }],
            "title": "Open"
          },
          "high": {
            "anyOf": [{ "type": "number" }, { "type": "null" }],
            "title": "High"
          },
          "low": {
            "anyOf": [{ "type": "number" }, { "type": "null" }],
            "title": "Low"
          },
          "close": {
            "anyOf": [{ "type": "number" }, { "type": "null" }],
            "title": "Close"
          },
          "volume": {
            "anyOf": [{ "type": "number" }, { "type": "null" }],
            "title": "Volume"
          }
        },
        "type": "object",
        "required": [
          "date",
          "symbol",
          "open",
          "high",
          "low",
          "close",
          "volume"
        ],
        "title": "StockDataItem"
      },
      "StockSymbol": {
        "properties": { "symbol": { "type": "string", "title": "Symbol" } },
        "type": "object",
        "required": ["symbol"],
        "title": "StockSymbol"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": { "anyOf": [{ "type": "string" }, { "type": "integer" }] },
            "type": "array",
            "title": "Location"
          },
          "msg": { "type": "string", "title": "Message" },
          "type": { "type": "string", "title": "Error Type" },
          "input": { "title": "Input" },
          "ctx": { "type": "object", "title": "Context" }
        },
        "type": "object",
        "required": ["loc", "msg", "type"],
        "title": "ValidationError"
      }
    }
  }
}
```

## 需求

建立一个 html 文件，里面是这些数据的折线图

1. 根据 api 文档，获取这几个 series_id 的数据：WALCL、WTREGEN、RRPONTSYD、TOTRESNS
