datas = []

datas.append(
    {
        'name': '123',
        'raw': 123,
    },
)

import json
f = json.dumps(datas, indent = 4)

print(f)