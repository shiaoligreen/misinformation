┌─────────────────────────────────────────────────────┐
│                    BROWSER                          │
│                                                     │
│  index.html loads                                   │
│       ↓                                             │
│  <link> pulls in styles.css                         │
│  <script> pulls in app.js                           │
│       ↓                                             │
│  User sees form, fills it in, hits Submit           │
│       ↓                                             │
│  app.js intercepts the submit event                 │
│  (prevents default page reload)                     │
│       ↓                                             │
│  app.js builds a GET request URL:                   │
│  http://localhost:8000/search?query=hello&mode=text │
│       ↓                                             │
│  fetch() sends that request →→→→→→→→→→→→→→→→→→→→→→ │
└─────────────────────────────────────────────────────┘
                                                      ↓
┌─────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                    │
│                                                     │
│  Route /search receives the GET request             │
│       ↓                                             │
│  Reads query params (query="hello", mode="text")    │
│       ↓                                             │
│  Calls corpus.py or annotations.py functions        │
│  (corpus already loaded in memory at startup)       │
│       ↓                                             │
│  Returns JSON:                                      │
│  { "results": ["sentence 1", "sentence 2", ...] }  │
│       ↓                                             │
│  ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← │
└─────────────────────────────────────────────────────┘
                                                      ↓
┌─────────────────────────────────────────────────────┐
│                    BROWSER                          │
│                                                     │
│  fetch() receives the JSON response                 │
│       ↓                                             │
│  app.js parses the JSON                             │
│       ↓                                             │
│  app.js dynamically builds HTML elements            │
│  and injects them into a <div id="results">         │
│       ↓                                             │
│  styles.css classes (e.g. .result-card) are         │
│  applied to those new elements                      │
│       ↓                                             │
│  User sees results — no page reload ever happened   │
└─────────────────────────────────────────────────────┘
