# app.py
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from itertools import count

app = Flask(__name__)

DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
MEALS = ["มื้อเช้า", "มื้อกลางวัน", "มื้อเย็น", "ของว่าง"]
MEAL_ORDER = {m: i for i, m in enumerate(MEALS)}

# เป้าหมายสารอาหารต่อวัน (ปรับได้)
TARGET = {"calories": 2000, "protein": 60, "carbs": 300, "fat": 65}

_id = count(1)

def new_item(day, meal, name, cal, pro, carb, fat):
    return {
        "id": next(_id), "day": day, "meal": meal, "name": name,
        "calories": float(cal), "protein": float(pro),
        "carbs": float(carb), "fat": float(fat),
    }

MENU = [
    new_item("จันทร์", "มื้อเช้า", "ข้าวต้มหมู + ไข่ต้ม", 350, 22, 45, 9),
    new_item("จันทร์", "มื้อกลางวัน", "ข้าวมันไก่", 600, 30, 70, 22),
    new_item("จันทร์", "มื้อเย็น", "สลัดอกไก่ย่าง", 320, 35, 18, 11),
    new_item("จันทร์", "ของว่าง", "กล้วยน้ำว้า 2 ผล", 180, 2, 45, 0.5),
    new_item("อังคาร", "มื้อเช้า", "ขนมปังโฮลวีท + ไข่ดาว", 380, 18, 40, 16),
    new_item("อังคาร", "มื้อกลางวัน", "ก๋วยเตี๋ยวเรือหมู", 450, 25, 55, 14),
    new_item("อังคาร", "มื้อเย็น", "แกงจืดเต้าหู้หมูสับ + ข้าวกล้อง", 480, 28, 60, 13),
    new_item("พุธ", "มื้อเช้า", "โจ๊กหมู", 300, 16, 42, 7),
    new_item("พุธ", "มื้อกลางวัน", "ผัดกะเพราไก่ไข่ดาว", 720, 34, 75, 32),
    new_item("พุธ", "มื้อเย็น", "ปลาเผา + น้ำจิ้มซีฟู้ด", 350, 40, 8, 16),
    new_item("พฤหัสบดี", "มื้อกลางวัน", "ข้าวหมูทอดกระเทียม", 680, 32, 72, 28),
    new_item("ศุกร์", "มื้อกลางวัน", "ส้มตำไทย + ไก่ย่าง + ข้าวเหนียว", 650, 33, 68, 24),
    new_item("เสาร์", "มื้อเย็น", "สุกี้น้ำรวมมิตร", 420, 30, 38, 15),
    new_item("อาทิตย์", "มื้อเช้า", "โยเกิร์ตกรีก + กราโนล่า", 310, 18, 36, 10),
]


def totals(items):
    t = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for it in items:
        for k in t:
            t[k] += it[k]
    return t


TEMPLATE = """
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ตารางเมนูอาหารรายวัน</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>body{font-family:'Noto Sans Thai',sans-serif}</style>
</head>
<body class="bg-slate-100 text-slate-800">
<div class="max-w-6xl mx-auto px-4 py-8">

  <header class="mb-6">
    <h1 class="text-3xl font-bold text-slate-900">ตารางเมนูอาหารรายวัน</h1>
    <p class="text-slate-500 mt-1">วางแผนมื้ออาหารพร้อมดูพลังงานและสารอาหารที่ได้รับในแต่ละวัน</p>
  </header>

  <!-- ตัวเลือกวัน -->
  <div class="flex flex-wrap gap-2 mb-6">
    <a href="{{ url_for('index') }}"
       class="px-4 py-2 rounded-full text-sm font-medium transition
       {{ 'bg-slate-900 text-white' if not selected_day else 'bg-white text-slate-600 hover:bg-slate-200' }}">
       ทุกวัน
    </a>
    {% for d in days %}
    <a href="{{ url_for('index', day=d) }}"
       class="px-4 py-2 rounded-full text-sm font-medium transition
       {{ 'bg-slate-900 text-white' if selected_day == d else 'bg-white text-slate-600 hover:bg-slate-200' }}">
       {{ d }}
    </a>
    {% endfor %}
  </div>

  <!-- การ์ดสรุป -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
    {% for key, label, unit, color in [
        ('calories','พลังงาน','kcal','bg-orange-500'),
        ('protein','โปรตีน','g','bg-rose-500'),
        ('carbs','คาร์โบไฮเดรต','g','bg-amber-500'),
        ('fat','ไขมัน','g','bg-sky-500')] %}
    {% set val = summary[key] %}
    {% set pct = (val / target[key] * 100) if target[key] else 0 %}
    <div class="bg-white rounded-2xl shadow-sm p-5">
      <p class="text-sm text-slate-500">{{ label }}</p>
      <p class="text-2xl font-bold mt-1">{{ '%.0f'|format(val) }}
        <span class="text-base font-normal text-slate-400">{{ unit }}</span></p>
      <div class="h-2 bg-slate-200 rounded-full mt-3 overflow-hidden">
        <div class="h-full {{ color }} rounded-full" style="width: {{ [pct, 100]|min }}%"></div>
      </div>
      <p class="text-xs text-slate-400 mt-2">
        {{ '%.0f'|format(pct) }}% ของเป้าหมาย {{ target[key] }} {{ unit }}{{ ' /วัน' if selected_day else '' }}
      </p>
    </div>
    {% endfor %}
  </div>

  <!-- ตารางเมนู -->
  <div class="bg-white rounded-2xl shadow-sm overflow-hidden mb-8">
    <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
      <h2 class="font-semibold text-lg">
        เมนู{{ 'วัน' + selected_day if selected_day else 'ทั้งสัปดาห์' }}
      </h2>
      <span class="text-sm text-slate-400">{{ items|length }} รายการ</span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-slate-500 uppercase text-xs">
          <tr>
            <th class="text-left px-6 py-3">วัน</th>
            <th class="text-left px-4 py-3">มื้อ</th>
            <th class="text-left px-4 py-3">เมนู</th>
            <th class="text-right px-4 py-3">พลังงาน (kcal)</th>
            <th class="text-right px-4 py-3">โปรตีน (g)</th>
            <th class="text-right px-4 py-3">คาร์บ (g)</th>
            <th class="text-right px-4 py-3">ไขมัน (g)</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
        {% for it in items %}
          <tr class="hover:bg-slate-50">
            <td class="px-6 py-3 text-slate-500">{{ it.day }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-1 rounded-md text-xs font-medium
                {{ {'มื้อเช้า':'bg-amber-100 text-amber-700',
                    'มื้อกลางวัน':'bg-emerald-100 text-emerald-700',
                    'มื้อเย็น':'bg-indigo-100 text-indigo-700',
                    'ของว่าง':'bg-pink-100 text-pink-700'}[it.meal] }}">
                {{ it.meal }}
              </span>
            </td>
            <td class="px-4 py-3 font-medium text-slate-900">{{ it.name }}</td>
            <td class="px-4 py-3 text-right font-semibold">{{ '%.0f'|format(it.calories) }}</td>
            <td class="px-4 py-3 text-right">{{ '%g'|format(it.protein) }}</td>
            <td class="px-4 py-3 text-right">{{ '%g'|format(it.carbs) }}</td>
            <td class="px-4 py-3 text-right">{{ '%g'|format(it.fat) }}</td>
            <td class="px-4 py-3 text-right">
              <a href="{{ url_for('delete', item_id=it.id, day=selected_day or '') }}"
                 class="text-slate-300 hover:text-red-500 font-bold">&times;</a>
            </td>
          </tr>
        {% else %}
          <tr><td colspan="8" class="px-6 py-10 text-center text-slate-400">ยังไม่มีเมนูในวันนี้</td></tr>
        {% endfor %}
        </tbody>
        {% if items %}
        <tfoot class="bg-slate-50 font-semibold">
          <tr>
            <td colspan="3" class="px-6 py-3 text-right">รวม</td>
            <td class="px-4 py-3 text-right">{{ '%.0f'|format(summary.calories) }}</td>
            <td class="px-4 py-3 text-right">{{ '%g'|format(summary.protein) }}</td>
            <td class="px-4 py-3 text-right">{{ '%g'|format(summary.carbs) }}</td>
            <td class="px-4 py-3 text-right">{{ '%g'|format(summary.fat) }}</td>
            <td></td>
          </tr>
        </tfoot>
        {% endif %}
      </table>
    </div>
  </div>

  <!-- ฟอร์มเพิ่มเมนู -->
  <div class="bg-white rounded-2xl shadow-sm p-6">
    <h2 class="font-semibold text-lg mb-4">เพิ่มเมนูใหม่</h2>
    <form method="post" action="{{ url_for('add') }}" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="col-span-1">
        <label class="block text-xs text-slate-500 mb-1">วัน</label>
        <select name="day" class="w-full border border-slate-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-slate-900 outline-none">
          {% for d in days %}<option {{ 'selected' if d == selected_day }}>{{ d }}</option>{% endfor %}
        </select>
      </div>
      <div class="col-span-1">
        <label class="block text-xs text-slate-500 mb-1">มื้อ</label>
        <select name="meal" class="w-full border border-slate-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-slate-900 outline-none">
          {% for m in meals %}<option>{{ m }}</option>{% endfor %}
        </select>
      </div>
      <div class="col-span-2">
        <label class="block text-xs text-slate-500 mb-1">ชื่อเมนู</label>
        <input name="name" required placeholder="เช่น ข้าวผัดกุ้ง"
               class="w-full border border-slate-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-slate-900 outline-none">
      </div>
      {% for f, lb in [('calories','พลังงาน (kcal)'),('protein','โปรตีน (g)'),('carbs','คาร์โบไฮเดรต (g)'),('fat','ไขมัน (g)')] %}
      <div>
        <label class="block text-xs text-slate-500 mb-1">{{ lb }}</label>
        <input type="number" step="0.1" min="0" name="{{ f }}" value="0"
               class="w-full border border-slate-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-slate-900 outline-none">
      </div>
      {% endfor %}
      <div class="col-span-2 md:col-span-4">
        <button class="bg-slate-900 text-white px-6 py-2.5 rounded-lg hover:bg-slate-700 transition font-medium">
          บันทึกเมนู
        </button>
      </div>
    </form>
  </div>

  <p class="text-center text-xs text-slate-400 mt-8">
    ข้อมูลสารอาหารเป็นค่าประมาณ &middot; API: <code>/api/menu</code>, <code>/api/summary</code>
  </p>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    day = request.args.get("day") or None
    if day not in DAYS:
        day = None
    items = [i for i in MENU if i["day"] == day] if day else list(MENU)
    items.sort(key=lambda x: (DAYS.index(x["day"]), MEAL_ORDER.get(x["meal"], 99)))
    return render_template_string(
        TEMPLATE, items=items, days=DAYS, meals=MEALS,
        selected_day=day, summary=totals(items), target=TARGET,
    )


@app.route("/add", methods=["POST"])
def add():
    f = request.form
    try:
        MENU.append(new_item(
            f.get("day", DAYS[0]), f.get("meal", MEALS[0]), f.get("name", "").strip() or "ไม่ระบุ",
            f.get("calories") or 0, f.get("protein") or 0,
            f.get("carbs") or 0, f.get("fat") or 0,
        ))
    except ValueError:
        pass
    return redirect(url_for("index", day=f.get("day")))


@app.route("/delete/<int:item_id>")
def delete(item_id):
    global MENU
    MENU = [i for i in MENU if i["id"] != item_id]
    return redirect(url_for("index", day=request.args.get("day") or None))


@app.route("/api/menu")
def api_menu():
    day = request.args.get("day")
    data = [i for i in MENU if i["day"] == day] if day in DAYS else MENU
    return jsonify(data)


@app.route("/api/summary")
def api_summary():
    result = {}
    for d in DAYS:
        t = totals([i for i in MENU if i["day"] == d])
        t["percent_calories"] = round(t["calories"] / TARGET["calories"] * 100, 1)
        result[d] = {k: round(v, 1) for k, v in t.items()}
    return jsonify({"target": TARGET, "daily": result})


if __name__ == "__main__":
    app.run(debug=True, port=5000)