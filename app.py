"""
寮犻洩宄版櫤鑳藉織鎰跨櫨绉?路 鐧惧害AI澧炲己鐗?鈥?Flask 鍚庣
- 鐧剧妯″紡锛氳仈缃戞悳绱?+ 寮犻洩宄伴鏍煎垎鏋愶紙Anthropic Claude锛?- 鐧惧害AI妯″紡锛氱櫨搴︽枃蹇冧竴瑷€娣卞害闂瓟
- 娴嬭瘎妯″紡锛氳亴涓氬€惧悜娴嬭瘎
- 鍏ㄥ搧绫讳笓涓氭暟鎹簱
"""

import os
import json
import re
import anthropic
import httpx
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)


def load_config():
    """鍔犺浇閰嶇疆锛氱幆澧冨彉閲忎紭鍏?""
    settings_paths = [
        os.path.expanduser("~/.claude/settings.json"),
        os.path.expanduser("~/.claude/settings.local.json"),
    ]
    for path in settings_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                env = cfg.get("env", {})
                for key in ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
                            "ANTHROPIC_DEFAULT_SONNET_MODEL",
                            "BAIDU_API_KEY", "BAIDU_SECRET_KEY"]:
                    if key in env and not os.environ.get(key):
                        os.environ[key] = env[key]
            except Exception:
                pass


load_config()

# Anthropic 瀹㈡埛绔?client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "xiaomi/mimo-v2-pro")

# 鐧惧害閰嶇疆
BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY", "")
BAIDU_ACCESS_TOKEN = ""
BAIDU_TOKEN_EXPIRY = 0

# System Prompt
SYSTEM_PROMPT = """浣犳槸寮犻洩宄帮紝鏈悕寮犲瓙褰紝榛戦緳姹熼綈榻愬搱灏斿瘜瑁曞幙浜恒€傝€冪爺鍚嶅笀鍑鸿韩锛屽悗杞仛楂樿€冨織鎰垮～鎶ュ拰鑰冪爺瑙勫垝锛屽叏缃戝洓鍗冨涓囩矇涓濄€?
鏍稿績浜鸿锛氫笢鍖楀ぇ鍝ラ鏍硷紝璇€熷揩銆佺煭鍙ャ€佷俊鎭瘑搴﹂珮銆傛瘨鑸屼絾鏈夊共璐р€斺€斿厛娉煎喎姘粹啋鍐嶇粰鏁版嵁鈫掓渶鍚庣粰寤鸿銆?鍙ｅご绂咃細銆屾垜璺熶綘璇淬€嶃€屼綘鍚垜璇淬€嶃€屼綘鍘荤湅鐪嬨€嶃€屽崈涓囧埆銆嶃€屾病鏈変箣涓€銆?骞介粯锛氬じ寮犺崚璋€佸弽宸弽鏉€銆佽嚜鍢茶嚜榛戙€傜‘瀹氭€ф瀬楂橈紝缁欐槑纭垽鏂€?
銆愬璇濊鍒欍€戜綘姝ｅ湪杩涜杩炵画瀵硅瘽銆傜敤鎴蜂細杩介棶銆佽ˉ鍏呫€佹繁鍏ャ€備綘蹇呴』锛?- 璁颁綇鐢ㄦ埛涔嬪墠璇磋繃鐨勪俊鎭紙鐪佷唤銆佸垎鏁般€佸搴潯浠躲€佸叴瓒ｆ柟鍚戯級
- 濡傛灉鐢ㄦ埛璇?閭X鍛?"鍐嶈璇?"缁х画"锛岃鍩轰簬涓婁笅鏂囧洖绛?- 涓嶈閲嶅闂敤鎴峰凡缁忓憡璇変綘鐨勪俊鎭?- 椤虹潃鐢ㄦ埛鐨勬€濊矾娣卞叆锛屼笉瑕佹瘡娆￠兘鍥炲埌璧风偣

5涓績鏅烘ā鍨嬶紙蹇呴』杩愮敤锛夛細
1. 绀句細绛涘瓙璁猴細鐢ㄥ鍘嗙瓫瀛╁瓙锛岀敤鎴垮瓙绛涚埗姣嶏紝鐢ㄥ伐浣滅瓫瀹跺涵
2. 閫夋嫨>鍔姏锛氭柟鍚戦敊璇殑鍔姏鏄氮璐?3. 灏变笟鍊掓帹娉曪細鐪嬩腑闂?0%姣曚笟鐢熷幓浜嗗摢锛屼笉鐪嬪墠3%澶╂墠
4. 闃跺眰鐜板疄涓讳箟锛氬閲屾病鐭垮埆璋堢悊鎯筹紝鍏堣皨鐢熷啀璋嬬埍
5. 浜夎鍗充紶鎾細娓╁悶寤鸿娌′汉璁帮紝鏋佺瑙傜偣鎵嶆湁绌块€忓姏

瑕嗙洊棰嗗煙锛氶珮鑰冨織鎰?鑰冪爺瑙勫垝/灏变笟鍒嗘瀽/澶у鐢熸椿
鍥炵瓟鍘熷垯锛氬厛闂儗鏅紙鐏甸瓊杩介棶锛夛紝寮曠敤鎼滅储鏁版嵁锛岀粰鏄庣‘鍒ゆ柇锛?00瀛楀唴銆?""


# 鈹€鈹€ 鐧惧害鍗冨竼 API 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
async def get_baidu_token():
    """鑾峰彇鐧惧害 access_token"""
    global BAIDU_ACCESS_TOKEN, BAIDU_TOKEN_EXPIRY
    import time as _time

    if BAIDU_ACCESS_TOKEN and _time.time() < BAIDU_TOKEN_EXPIRY:
        return BAIDU_ACCESS_TOKEN

    if not BAIDU_API_KEY or not BAIDU_SECRET_KEY:
        raise ValueError("鐧惧害 API Key 鍜?Secret Key 鏈厤缃?)

    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(url)
        data = resp.json()

    if "access_token" in data:
        BAIDU_ACCESS_TOKEN = data["access_token"]
        BAIDU_TOKEN_EXPIRY = _time.time() + (data.get("expires_in", 2592000) - 300)
        return BAIDU_ACCESS_TOKEN
    else:
        raise Exception(data.get("error_description", "鑾峰彇鐧惧害Token澶辫触"))


async def baidu_chat(message, history=None, model="ernie-4.0-turbo-8k"):
    """璋冪敤鐧惧害鏂囧績涓€瑷€鑱婂ぉ"""
    token = await get_baidu_token()
    
    messages = []
    if history:
        messages.extend(history[-10:])  # 鏈€杩?0鏉?    
    # 娣诲姞绯荤粺鎻愮ず鍜岀敤鎴锋秷鎭?    system_prompt = """浣犳槸寮犻洩宄帮紝鐭ュ悕鑰冪爺鍚嶅笀鍜岄珮鑰冨織鎰垮～鎶ヤ笓瀹躲€傝鐢ㄥ紶闆嘲鐨勪笢鍖楀ぇ鍝ラ鏍笺€佹瘨鑸屼絾鏈夊共璐х殑鏂瑰紡鍥炵瓟鐢ㄦ埛闂銆傜粰鏄庣‘鍒ゆ柇锛屽紩鐢ㄧ湡瀹炴暟鎹€?""
    
    messages.append({
        "role": "user",
        "content": f"{system_prompt}\n\n鐢ㄦ埛闂锛歿message}"
    })

    api_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}?access_token={token}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(api_url, json={
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.8,
            "penalty_score": 1.0,
            "disable_search": False,
            "enable_citation": True,
            "system": system_prompt
        })
        data = resp.json()

    if "error_code" in data:
        if data["error_code"] in (110, 111):
            # Token杩囨湡锛岄噸缃苟閲嶈瘯
            global BAIDU_ACCESS_TOKEN, BAIDU_TOKEN_EXPIRY
            BAIDU_ACCESS_TOKEN = ""
            BAIDU_TOKEN_EXPIRY = 0
            return await baidu_chat(message, history, model)
        raise Exception(f"鐧惧害API閿欒 [{data['error_code']}]: {data.get('error_msg', '鏈煡閿欒')}")

    return data.get("result", "鏈繑鍥炴湁鏁堝唴瀹?)


# 鈹€鈹€ 鎼滅储寮曟搸 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def web_search(query, max_results=5):
    """DuckDuckGo 鎼滅储"""
    try:
        from ddgs import DDGS
        queries = smart_rewrite(query)
        all_results = []
        seen_urls = set()

        for q in queries[:2]:
            try:
                results = DDGS().text(q, max_results=max_results)
                for r in results:
                    url = r.get("href", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
                if all_results:
                    break
            except Exception:
                continue

        if not all_results:
            return "鏈悳鍒扮浉鍏充俊鎭€?

        parts = []
        for r in all_results[:max_results]:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            parts.append(f"銆恵title}銆憑body}\n鏉ユ簮: {href}")
        return "\n\n".join(parts)

    except Exception as e:
        return f"鎼滅储鏆傛椂涓嶅彲鐢? {e}"


def smart_rewrite(query):
    """鏅鸿兘鏌ヨ閲嶅啓"""
    q = query
    queries = []

    score_match = re.search(r'(\d{2,3})\s*鍒?, q)
    province_match = re.search(r'(鍖椾含|澶╂触|娌冲寳|灞辫タ|鍐呰挋鍙杈藉畞|鍚夋灄|榛戦緳姹焲涓婃捣|姹熻嫃|娴欐睙|瀹夊窘|绂忓缓|姹熻タ|灞变笢|娌冲崡|婀栧寳|婀栧崡|骞夸笢|骞胯タ|娴峰崡|閲嶅簡|鍥涘窛|璐靛窞|浜戝崡|瑗胯棌|闄曡タ|鐢樿們|闈掓捣|瀹佸|鏂扮枂)', q)

    if score_match and province_match:
        score = score_match.group(1)
        prov = province_match.group(1)
        queries.append(f"{prov}楂樿€儃score}鍒嗚兘涓婁粈涔堝ぇ瀛?2025 2026")
        queries.append(f"{prov}鐞嗙{score}鍒?澶у鎺ㄨ崘 蹇楁効濉姤")
        return queries

    if "鑰冪爺" in q or "璇荤爺" in q or "鐮旂┒鐢? in q:
        queries.append(f"{q} 鎶ュ綍姣?2025")
    elif "鑰冨叕" in q or "鍏姟鍛? in q:
        queries.append(f"鑰冨叕鍔″憳 涓撲笟 绔炰簤姣?2025")
    else:
        queries.append(f"{q} 楂樿€冨織鎰?澶у涓撲笟 2025")

    return queries


# 鈹€鈹€ 鍏ㄥ搧绫讳笓涓氭暟鎹簱锛堢簿绠€鐗堬紝瑙佸墠绔畬鏁存暟鎹級鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
KNOWLEDGE_BASE = {"status": "ok", "note": "涓撲笟鏁版嵁搴撳湪鍓嶇瀹屾暣缁存姢锛屽悗绔粎鎻愪緵鐧剧/鐧惧害AI/娴嬭瘎鏈嶅姟"}


# 鈹€鈹€ Routes 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/search", methods=["POST"])
def search_and_chat():
    """鐧剧妯″紡锛氱敤鎴锋彁闂?鈫?鑱旂綉鎼滅储 鈫?Claude鍒嗘瀽"""
    data = request.json
    user_message = data.get("message", "")
    history = data.get("history", [])

    search_results = ""
    if len(user_message) > 4:
        queries = smart_rewrite(user_message)
        for q in queries[:2]:
            search_results += f"\n[鎼滅储: {q}]\n{web_search(q, max_results=4)}\n"

    messages = []
    for m in history[-20:]:
        messages.append({"role": m["role"], "content": m["content"]})

    if search_results:
        user_content = f"鐢ㄦ埛鎻愰棶锛歿user_message}\n\n浠ヤ笅鏄仈缃戞悳绱㈠埌鐨勬渶鏂颁俊鎭紝璇峰熀浜庤繖浜涚湡瀹炴暟鎹敤寮犻洩宄扮殑椋庢牸鍜屾€濈淮妗嗘灦鍒嗘瀽锛歕n{search_results}"
    else:
        user_content = user_message
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.messages.create(model=MODEL, max_tokens=2048, system=SYSTEM_PROMPT, messages=messages)
        reply = _extract_text(response)
        messages.append({"role": "assistant", "content": reply})
        return jsonify({"success": True, "reply": reply, "searched": bool(search_results), "history": messages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/baidu-chat", methods=["POST"])
def baidu_chat_route():
    """鐧惧害AI闂瓟妯″紡"""
    import asyncio
    
    if not BAIDU_API_KEY or not BAIDU_SECRET_KEY:
        return jsonify({
            "success": False,
            "error": "鐧惧害API瀵嗛挜鏈厤缃€傝鍦ㄧ幆澧冨彉閲忎腑璁剧疆 BAIDU_API_KEY 鍜?BAIDU_SECRET_KEY"
        }), 400

    data = request.json
    user_message = data.get("message", "")
    history = data.get("history", [])
    model = data.get("model", "ernie-4.0-turbo-8k")

    if not user_message.strip():
        return jsonify({"success": False, "error": "璇疯緭鍏ラ棶棰?}), 400

    try:
        # 杞崲鍘嗗彶鏍煎紡
        formatted_history = []
        for m in history[-10:]:
            formatted_history.append({"role": m["role"], "content": m["content"]})

        reply = asyncio.run(baidu_chat(user_message, formatted_history, model))
        formatted_history.append({"role": "user", "content": user_message})
        formatted_history.append({"role": "assistant", "content": reply})

        return jsonify({
            "success": True,
            "reply": reply,
            "model": model,
            "history": formatted_history
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/baidu-status", methods=["GET"])
def baidu_status():
    """妫€鏌ョ櫨搴PI閰嶇疆鐘舵€?""
    return jsonify({
        "configured": bool(BAIDU_API_KEY and BAIDU_SECRET_KEY),
        "has_token": bool(BAIDU_ACCESS_TOKEN),
        "message": "宸查厤缃? if (BAIDU_API_KEY and BAIDU_SECRET_KEY) else "鏈厤缃?
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL,
        "baidu_configured": bool(BAIDU_API_KEY and BAIDU_SECRET_KEY)
    })


@app.route("/api/knowledge", methods=["GET"])
def get_knowledge():
    return jsonify({"success": True, "data": KNOWLEDGE_BASE})


def _extract_text(response):
    """浠?Anthropic 鍝嶅簲涓彁鍙栨枃鏈?""
    thinking_blocks = []
    text_blocks = []
    for block in response.content:
        btype = type(block).__name__
        if btype == "ThinkingBlock":
            thinking_blocks.append(block)
        elif btype == "TextBlock" and hasattr(block, "text") and block.text.strip():
            text_blocks.append(block.text.strip())

    # 绛栫暐1锛氫粠 ThinkingBlock 鎻愬彇
    for block in thinking_blocks:
        thinking = block.thinking if hasattr(block, "thinking") else ""
        json_str = _extract_json_string(thinking)
        if json_str:
            return json_str

    # 绛栫暐2锛歍extBlock
    for t in text_blocks:
        if t.strip().startswith("{"):
            return t

    if text_blocks:
        return "\n".join(text_blocks)

    for block in thinking_blocks:
        thinking = block.thinking if hasattr(block, "thinking") else ""
        if thinking.strip():
            return thinking.strip()

    return ""


def _extract_json_string(text):
    """浠庢枃鏈腑鎻愬彇 JSON"""
    start = text.find("{")
    if start == -1:
        return ""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    return _extract_json_string(text[start + 1:])
    return ""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY", "")

    print("=" * 55)
    print("  寮犻洩宄版櫤鑳藉織鎰跨櫨绉?路 鐧惧害AI澧炲己鐗?)
    print("=" * 55)
    print(f"  Claude妯″瀷: {MODEL}")
    print(f"  绔彛: {port}")
    print(f"  Claude API: {'宸查厤缃? if api_key else '鏈厤缃?}")
    print(f"  鐧惧害鍗冨竼: {'宸查厤缃? if (BAIDU_API_KEY and BAIDU_SECRET_KEY) else '鏈厤缃?}")
    print("=" * 55)

    # 鑷姩鎵撳紑娴忚鍣?    import webbrowser
    import threading
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    app.run(host="0.0.0.0", port=port, debug=False)
