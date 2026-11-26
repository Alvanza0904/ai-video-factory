#!/usr/bin/env python3
"""Free-first Indonesian 2D educational animation renderer."""
import json, math, os, subprocess, sys, urllib.parse, urllib.request, urllib.error
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path.cwd()
WORK = ROOT / "education-work"
OUT = ROOT / "ai-video-factory-final.mp4"
W, H, FPS = 540, 960, 15
MODEL = Path(os.environ.get("PIPER_MODEL", "models/id_ID-news_tts-medium.onnx"))
ACTIVE_BRAND = "JAECOO"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TOPICS = {
 "regenerative braking": [
  ("Pernah kepikiran, kenapa mobil listrik bisa mengembalikan sebagian energi saat melambat?", "car", "REGENERATIVE BRAKING"),
  ("Saat pengemudi melepas pedal gas atau mengerem, motor listrik dapat bekerja seperti generator.", "motor", "MOTOR JADI GENERATOR"),
  ("Energi gerak roda diubah menjadi energi listrik, lalu dialirkan kembali menuju baterai.", "energy", "ENERGI KEMBALI KE BATERAI"),
  ("Tapi bukan berarti mobil menciptakan energi baru. Sebagian energi tetap hilang sebagai panas dan hambatan.", "battery", "BUKAN ENERGI GRATIS"),
  ("Seberapa banyak energi yang pulih bergantung pada kecepatan, kondisi jalan, baterai, dan pengaturan kendaraan.", "car", "TERGANTUNG KONDISI"),
  ("Itulah regenerative braking: membantu efisiensi perjalanan sekaligus membuat pengalaman berkendara lebih terkendali.", "energy", "LEBIH EFISIEN")
 ],
 "baterai lfp": [
  ("Baterai mobil listrik punya beberapa jenis kimia. Salah satu yang sering dibahas adalah LFP.", "battery", "MENGENAL BATERAI LFP"),
  ("LFP adalah singkatan dari lithium iron phosphate, yaitu lithium, besi, dan fosfat.", "chemistry", "LITHIUM IRON PHOSPHATE"),
  ("Kimia ini dikenal memiliki stabilitas termal yang baik dan umur siklus yang relatif panjang.", "battery", "STABILITAS TERMAL"),
  ("Namun, seperti baterai lain, performanya dipengaruhi suhu, cara pengisian, penggunaan, dan sistem pengelolaan baterai.", "temperature", "SUHU TETAP PENTING"),
  ("Kapasitas, jarak tempuh, dan kecepatan pengisian tidak bisa disimpulkan hanya dari jenis kimia baterainya.", "charging", "BUKAN HANYA JENIS BATERAI"),
  ("Jadi, saat membandingkan mobil listrik, lihat juga kapasitas, garansi, sistem pendingin, dan spesifikasi resminya.", "checklist", "CEK SPESIFIKASI LENGKAP")
 ],
 "bev hev phev": [
  ("BEV, HEV, dan PHEV terdengar mirip. Tapi cara kerja dan sumber energinya berbeda.", "threecars", "BEV • HEV • PHEV"),
  ("BEV adalah mobil listrik murni. Roda digerakkan motor listrik dan energi utamanya berasal dari baterai.", "battery", "BEV: LISTRIK MURNI"),
  ("HEV menggabungkan mesin bensin dan motor listrik. Baterainya umumnya diisi saat kendaraan berjalan dan mengerem.", "hybrid", "HEV: HYBRID"),
  ("PHEV juga menggabungkan mesin dan motor listrik, tetapi baterainya dapat diisi dari sumber listrik eksternal.", "charging", "PHEV: BISA DI-CHARGE"),
  ("Jadi, perbedaan pentingnya ada pada sumber tenaga dan apakah baterainya bisa diisi dari luar.", "threecars", "BEDA SISTEM, BEDA KEBUTUHAN"),
  ("Pilih berdasarkan pola perjalanan, akses pengisian, dan spesifikasi kendaraan yang benar-benar ditawarkan.", "checklist", "SESUAIKAN KEBUTUHAN")
 ],
 "ac dc charging": [
  ("Kenapa ada charger AC dan DC? Keduanya mengisi baterai, tetapi jalur listriknya berbeda.", "charging", "AC ATAU DC?"),
  ("Pada pengisian AC, listrik bolak-balik masuk ke kendaraan dan diubah menjadi arus searah oleh onboard charger.", "ac", "AC: DIUBAH DI MOBIL"),
  ("Pada pengisian DC, konversi utama dilakukan di stasiun pengisian sebelum listrik masuk ke baterai.", "dc", "DC: KONVERSI DI STASIUN"),
  ("Karena itu, pengisian DC umumnya bisa lebih cepat jika kendaraan dan stasiun mendukung dayanya.", "charging", "POTENSI LEBIH CEPAT"),
  ("Kecepatan nyata tetap dipengaruhi batas kendaraan, suhu baterai, tingkat isi, dan kondisi stasiun.", "battery", "KECEPATAN BISA BERUBAH"),
  ("Jadi, selalu cocokkan spesifikasi port, daya maksimum, dan rekomendasi pengisian kendaraanmu.", "checklist", "CEK KOMPATIBILITAS")
 ],
 "motor listrik": [
  ("Mobil listrik tidak perlu mesin pembakaran untuk menggerakkan roda. Lalu bagaimana mobil bisa melaju?", "car", "BAGAIMANA MOBIL MELAJU?"),
  ("Energi dari baterai dikirim ke inverter dan sistem pengendali sesuai kebutuhan pengemudi.", "battery", "ENERGI DARI BATERAI"),
  ("Inverter mengatur suplai listrik ke motor, termasuk mengubah arus searah baterai menjadi arus yang dibutuhkan motor.", "motor", "INVERTER MENGATUR DAYA"),
  ("Motor listrik mengubah energi listrik menjadi putaran mekanis yang menggerakkan roda melalui sistem transmisi reduksi.", "energy", "LISTRIK JADI GERAK"),
  ("Karena karakter torsi motor listrik, respons akselerasi bisa terasa cepat sejak kecepatan rendah.", "car", "RESPONS AKSELERASI"),
  ("Itulah alur sederhananya: baterai, pengendali daya, motor, lalu roda bergerak.", "checklist", "BATERAI → MOTOR → RODA")
 ]
}

def run(cmd, **kwargs):
    print("+", " ".join(map(str, cmd[:8])), flush=True)
    subprocess.run(cmd, check=True, **kwargs)

def fetch_manifest():
    job = os.environ["JOB_ID"]
    query = urllib.parse.urlencode({"job_id": job, "run_id": os.environ["GITHUB_RUN_ID"]})
    req = urllib.request.Request(os.environ["MANIFEST_URL"] + "?" + query,
        headers={"Authorization": "Bearer " + os.environ["OIDC_TOKEN"], "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))

def choose_script(topic, duration):
    key = topic.lower()
    if "regenerative" in key or "pengereman" in key or "rem" in key:
        scenes = TOPICS["regenerative braking"]
    elif "lfp" in key or "baterai" in key:
        scenes = TOPICS["baterai lfp"]
    elif "bev" in key or "phev" in key or "hev" in key or "hybrid" in key:
        scenes = TOPICS["bev hev phev"]
    elif "ac" in key or "dc" in key or "charging" in key or "pengisian" in key or "charger" in key:
        scenes = TOPICS["ac dc charging"]
    elif "motor" in key or "inverter" in key:
        scenes = TOPICS["motor listrik"]
    else:
        scenes = [
          ("Pernah bertanya bagaimana " + topic + " bekerja? Yuk, kita bahas dengan cara sederhana.", "question", "KITA BAHAS BERSAMA"),
          ("Pertama, kenali komponen utama dan fungsi masing-masing bagian sebelum melihat keseluruhan sistem.", "parts", "KENALI KOMPONENNYA"),
          ("Setiap komponen bekerja saling terhubung. Perubahan pada satu bagian dapat memengaruhi kinerja sistem.", "system", "SEMUA SALING TERHUBUNG"),
          ("Dalam penggunaan nyata, hasilnya dipengaruhi desain, kondisi, dan spesifikasi dari setiap kendaraan.", "car", "KONDISI MENENTUKAN"),
          ("Jangan hanya mengandalkan istilah atau klaim promosi. Periksa penjelasan dan spesifikasi dari sumber resmi.", "checklist", "PERIKSA SUMBER RESMI"),
          ("Sekarang kamu sudah punya gambaran dasar tentang " + topic + ". Simpan video ini untuk mengingat penjelasannya.", "question", "SEKARANG SUDAH TAHU")
        ]
    if duration == 30:
        scenes = [scenes[i] for i in (0, 1, 2, 4, 5)]
    return [{"narration": x[0], "visual": x[1], "title": x[2]} for x in scenes]

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def centered(draw, text, y, fnt, fill, maxw=470):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0,0), test, font=fnt)[2] <= maxw: line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    for ln in lines:
        box = draw.textbbox((0,0), ln, font=fnt)
        draw.text(((W-(box[2]-box[0]))/2, y), ln, font=fnt, fill=fill)
        y += fnt.size + 10
    return y

def rr(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_car(d, cx, cy, scale=1.0, accent="#B8F36A"):
    bw, bh = int(260*scale), int(94*scale)
    x, y = int(cx-bw/2), int(cy-bh/2)
    d.rounded_rectangle((x,y+30*scale,x+bw,y+bh), radius=int(26*scale), fill="#DCE8F2", outline="#FFFFFF", width=3)
    d.polygon([(x+45*scale,y+31*scale),(x+88*scale,y),(x+190*scale,y),(x+225*scale,y+31*scale)], fill="#9DC8E4")
    d.line([(x+88*scale,y+4*scale),(x+88*scale,y+31*scale),(x+190*scale,y+31*scale),(x+190*scale,y+4*scale)], fill="#4D657A", width=3)
    for wx in (x+58*scale,x+202*scale):
        d.ellipse((wx-22*scale,y+bh-8*scale,wx+22*scale,y+bh+36*scale), fill="#172334", outline="#9AAABD", width=4)
        d.ellipse((wx-8*scale,y+bh+6*scale,wx+8*scale,y+bh+22*scale), fill=accent)
    d.rounded_rectangle((x+8*scale,y+48*scale,x+30*scale,y+65*scale), radius=5, fill="#FFE8A3")
    d.rounded_rectangle((x+bw-30*scale,y+48*scale,x+bw-8*scale,y+65*scale), radius=5, fill="#FF7A72")

def draw_battery(d, cx, cy, progress, accent="#B8F36A"):
    x,y=cx-115,cy-95
    rr(d,(x,y,x+230,y+190),24,"#E8F0F5","#FFFFFF",4)
    rr(d,(x+230,y+62,x+252,y+128),8,"#E8F0F5")
    fill=max(0.08,min(.92,progress))
    d.rounded_rectangle((x+18,y+18,x+18+194*fill,y+172),radius=15,fill=accent)
    d.text((cx,y+90),"",font=font(20),fill="#172334")

def draw_person(d, cx, cy, phase):
    d.ellipse((cx-55,cy-130,cx+55,cy-20),fill="#F0C5A4",outline="#FFFFFF",width=3)
    d.arc((cx-62,cy-145,cx+62,cy-8),180,355,fill="#26364B",width=22)
    d.rounded_rectangle((cx-85,cy-10,cx+85,cy+190),radius=48,fill="#B8F36A",outline="#FFFFFF",width=3)
    arm_y=cy+45+int(math.sin(phase*math.pi*2)*12)
    d.line((cx-75,cy+20,cx-145,arm_y),fill="#F0C5A4",width=22)
    d.line((cx+75,cy+20,cx+145,arm_y-25),fill="#F0C5A4",width=22)
    d.ellipse((cx-22,cy-75,cx-8,cy-61),fill="#243044")
    d.ellipse((cx+8,cy-75,cx+22,cy-61),fill="#243044")
    d.arc((cx-18,cy-65,cx+18,cy-38),0,180,fill="#8E5148",width=3)

def draw_frame(scene, idx, total):
    p = idx / max(1,total-1)
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    top=(10,17,29); bottom=(19,35,51)
    for y in range(H):
        t=y/(H-1)
        col=tuple(int(top[i]*(1-t)+bottom[i]*t) for i in range(3))
        d.line((0,y,W,y),fill=col)
    accent="#B8F36A"; cyan="#65D8F2"; white="#F3F7FA"; muted="#A9B8C8"
    d.ellipse((-150,210,170,530),fill="#172C3C")
    d.ellipse((365,570,680,885),fill="#142B3A")
    rr(d,(28,34,W-28,79),18,"#1B2A37")
    d.text((48,47),"AUTO EDUCATION  /  EXPLAINED",font=font(15,True),fill=accent)
    centered(d,scene["title"],112,font(29,True),white,470)
    v=scene["visual"]
    cy=470
    if v in ("car","threecars","hybrid"):
        draw_car(d, int(270+math.sin(p*math.pi*2)*28), cy, .88, accent)
        if v=="threecars":
            for j,label in enumerate(("BEV","HEV","PHEV")):
                rr(d,(40+j*158,625,184+j*158,687),15,"#223B4D",outline=accent if j==0 else "#547084")
                centered(d,label,644,font(20,True),white,125)
        elif v=="hybrid":
            rr(d,(105,625,435,704),20,"#223B4D",outline=cyan)
            centered(d,"MESIN + MOTOR LISTRIK",650,font(17,True),white,300)
    elif v in ("battery","charging","temperature","chemistry"):
        draw_battery(d,270,450,.25+.7*p,accent)
        if v=="temperature":
            d.arc((180,650,360,830),190,350,fill="#FF9B72",width=14)
            centered(d,"SUHU • PENGGUNAAN • PERAWATAN",770,font(15,True),white,440)
        elif v=="charging":
            d.line((270,560,270,690),fill=cyan,width=9)
            d.polygon([(270,690),(252,660),(288,660)],fill=cyan)
    elif v in ("motor","energy","ac","dc","system","parts"):
        draw_car(d,270,590,.65,accent)
        d.ellipse((190,330,350,490),outline=cyan,width=9)
        d.arc((170,310,370,510),int(40+p*200),int(260+p*200),fill=accent,width=12)
        d.polygon([(350,380),(370,400),(340,405)],fill=accent)
        centered(d,{"motor":"MOTOR LISTRIK","energy":"ENERGI → GERAK","ac":"ARUS AC","dc":"ARUS DC","system":"SISTEM TERHUBUNG","parts":"KOMPONEN UTAMA"}[v],760,font(20,True),white,460)
    elif v=="question":
        draw_person(d,270,470,p)
        rr(d,(60,690,480,790),22,"#233A4B",outline=cyan)
        centered(d,"YUK, KITA PELAJARI!",720,font(21,True),white,380)
    elif v=="checklist":
        for j,label in enumerate(("KENALI TEKNOLOGINYA","CEK SPESIFIKASI","PAHAMI KEBUTUHAN")):
            y=340+j*115
            rr(d,(65,y,475,y+78),18,"#203747",outline=accent if j==0 else "#426073")
            d.ellipse((88,y+22,122,y+56),fill=accent)
            d.line((97,y+39,105,y+47,116,y+30),fill="#142334",width=5)
            d.text((140,y+27),label,font=font(16,True),fill=white)
    else:
        draw_person(d,270,450,p)
    # Kinetic accent: animated progress line and scene marker.
    d.rounded_rectangle((45,865,495,876),radius=5,fill="#314353")
    d.rounded_rectangle((45,865,45+int(450*p),876),radius=5,fill=accent)
    d.text((46,895),f"{ACTIVE_BRAND}  •  PALEMBANG",font=font(14,True),fill=muted)
    return img

def make_subtitles(scenes, voice_duration):
    total_words=sum(max(1,len(s["narration"].split())) for s in scenes)
    cursor=0.0
    lines=[]
    for i,s in enumerate(scenes,1):
        words=max(1,len(s["narration"].split()))
        duration=voice_duration*words/total_words
        start=cursor+0.05
        end=min(voice_duration,cursor+duration)
        text=s["narration"].replace("--","—")
        lines.append(f"{i}\n{stamp(start)} --> {stamp(max(start+0.6,end-0.08))}\n{text}\n")
        cursor+=duration
    path=WORK/"captions.srt"
    path.write_text("\n".join(lines),encoding="utf-8")
    return path

def stamp(seconds):
    ms=int(max(0,seconds)*1000)
    h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def piper_voice(text):
    if not MODEL.exists():
        raise RuntimeError("Model suara Bahasa Indonesia tidak ditemukan.")
    output=WORK/"narration.wav"
    proc=subprocess.run(["piper","--model",str(MODEL),"--output_file",str(output)],
        input=text,text=True,capture_output=True)
    if proc.returncode:
        raise RuntimeError("Piper TTS gagal: "+proc.stderr[-700:])
    if not output.exists() or output.stat().st_size<1000:
        raise RuntimeError("Piper tidak menghasilkan audio narasi.")
    return output

def main():
    global ACTIVE_BRAND
    WORK.mkdir(exist_ok=True)
    manifest=fetch_manifest()
    ACTIVE_BRAND=manifest["brand"]
    topic=manifest["topic"]
    brand=manifest["brand"]
    duration=int(manifest["duration"])
    scenes=choose_script(topic,duration)
    narration=" ".join(s["narration"] for s in scenes)
    print("Narration:",narration,flush=True)
    audio=piper_voice(narration)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(audio)]))
    voice_duration=float(probe["format"]["duration"])
    total_duration=voice_duration+1.8
    print(f"TTS duration {voice_duration:.2f}s; output {total_duration:.2f}s",flush=True)
    subs=make_subtitles(scenes,voice_duration)
    word_counts=[max(1,len(s["narration"].split())) for s in scenes]
    total_words=sum(word_counts)
    cursor=0.0
    clip_paths=[]
    for n,scene in enumerate(scenes,1):
        scene_duration=total_duration*word_counts[n-1]/total_words
        frames=max(30,round(scene_duration*FPS))
        folder=WORK/f"scene-{n:02d}"
        folder.mkdir(exist_ok=True)
        for frame in range(frames):
            draw_frame(scene,frame,frames).save(folder/f"frame-{frame:04d}.png",optimize=False)
        clip=WORK/f"scene-{n:02d}.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",str(FPS),
             "-i",str(folder/"frame-%04d.png"),"-vf","scale=1080:1920:flags=lanczos,fps=30,format=yuv420p",
             "-an","-c:v","libx264","-preset","ultrafast","-crf","24","-movflags","+faststart",str(clip)])
        clip_paths.append(clip)
        cursor+=scene_duration
    concat=WORK/"concat.txt"
    concat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in clip_paths),encoding="utf-8")
    silent=WORK/"silent.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),
         "-c","copy","-movflags","+faststart",str(silent)])
    music_expr=f"aevalsrc=0.018*sin(2*PI*220*t)+0.012*sin(2*PI*277.18*t)+0.008*sin(2*PI*329.63*t):s=48000:d={total_duration:.2f}"
    subtitle_arg=str(subs.resolve()).replace("\\","/").replace(":","\\:")
    vf=f"subtitles='{subtitle_arg}':force_style='FontName=DejaVu Sans,FontSize=15,Bold=1,Outline=2,Shadow=1,Alignment=2,MarginV=150,PrimaryColour=&H00FFFFFF,OutlineColour=&H90081720'"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),
         "-f","lavfi","-i",music_expr,"-filter_complex",
         "[1:a]volume=1.0[voice];[2:a]lowpass=f=600,volume=0.018[bed];[voice][bed]amix=inputs=2:duration=first:dropout_transition=1,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
         "-vf",vf,"-map","0:v:0","-map","[a]","-t",f"{total_duration:.2f}",
         "-r","30","-c:v","libx264","-preset","veryfast","-crf","22","-c:a","aac","-b:a","160k",
         "-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)])
    final=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_name,width,height","-of","json",str(OUT)]))
    video=next((s for s in final["streams"] if s.get("codec_name")=="h264"),None)
    if not video or video.get("width")!=1080 or video.get("height")!=1920:
        raise RuntimeError("Quality check gagal: output bukan H.264 1080x1920.")
    if OUT.stat().st_size<100000:
        raise RuntimeError("Quality check gagal: file MP4 terlalu kecil.")
    blueprint={"brand":brand,"topic":topic,"duration":float(final["format"]["duration"]),
        "style":"2D explainer + cartoon + motion graphics","voice":"Piper Indonesian news medium",
        "scenes":scenes}
    (WORK/"blueprint.json").write_text(json.dumps(blueprint,ensure_ascii=False,indent=2),encoding="utf-8")
    params=urllib.parse.urlencode({"job_id":manifest["jobId"],"user_id":manifest["userId"],
        "expires":manifest["expires"],"signature":manifest["signature"],"run_id":os.environ["GITHUB_RUN_ID"]})
    req=urllib.request.Request(os.environ["OUTPUT_UPLOAD_BASE_URL"]+"?"+params,data=OUT.read_bytes(),
        headers={"Content-Type":"video/mp4","Content-Length":str(OUT.stat().st_size),
        "Authorization":"Bearer "+os.environ["OIDC_TOKEN"],"User-Agent":"AI-Animated-Education-Factory"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=300) as response:
            result=json.loads(response.read().decode())
            if not result.get("success"): raise RuntimeError("R2 tidak mengonfirmasi unggahan video.")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Upload video ke R2 gagal (HTTP {error.code}).") from None
    print(f"SUCCESS: {brand} education video '{topic}' — {final['format']['duration']} sec, {OUT.stat().st_size} bytes.",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("EDUCATION ANIMATION FAILED:",str(exc),file=sys.stderr)
        sys.exit(1)
