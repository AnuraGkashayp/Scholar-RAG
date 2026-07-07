from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, ListFlowable, ListItem)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

# ---- palette ----
NAVY   = colors.HexColor("#0d2137")
BLUE   = colors.HexColor("#1e88e5")
GREEN  = colors.HexColor("#2e7d32")
ORANGE = colors.HexColor("#e65100")
PURPLE = colors.HexColor("#6a1b9a")
RED    = colors.HexColor("#b71c1c")
GREY   = colors.HexColor("#555555")
LIGHT  = colors.HexColor("#eef2f6")
CODEBG = colors.HexColor("#1a1a2e")

styles = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=24, textColor=NAVY,
                    spaceAfter=6, leading=28)
SUB = ParagraphStyle("SUB", parent=styles["Normal"], fontSize=12, textColor=GREY,
                     spaceAfter=14, leading=16)
H2 = ParagraphStyle("H2", parent=styles["Heading1"], fontSize=17, textColor=BLUE,
                    spaceBefore=14, spaceAfter=8, leading=20)
H3 = ParagraphStyle("H3", parent=styles["Heading2"], fontSize=13, textColor=NAVY,
                    spaceBefore=10, spaceAfter=5, leading=16)
BODY = ParagraphStyle("BODY", parent=styles["Normal"], fontSize=10.5, leading=15,
                      spaceAfter=7, alignment=TA_LEFT)
BULLET = ParagraphStyle("BULLET", parent=BODY, leftIndent=6, spaceAfter=3)
CODE = ParagraphStyle("CODE", parent=styles["Code"], fontSize=8.8, textColor=colors.white,
                      backColor=CODEBG, leading=12, leftIndent=8, rightIndent=8,
                      spaceBefore=4, spaceAfter=10, borderPadding=8)
NOTE = ParagraphStyle("NOTE", parent=BODY, fontSize=9.5, textColor=NAVY,
                      backColor=LIGHT, borderPadding=8, leading=14, spaceAfter=10)

story = []

def code(txt):
    safe = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<br/>").replace(" ", "&nbsp;")
    story.append(Paragraph(safe, CODE))

def bullets(items, style=BULLET):
    flow = [ListItem(Paragraph(t, style), leftIndent=12, value="•") for t in items]
    story.append(ListFlowable(flow, bulletType="bullet", start="•", leftIndent=14))
    story.append(Spacer(1, 4))

def box(title, rows, header_color):
    data = [[Paragraph(f"<b>{title}</b>", ParagraphStyle('t', parent=BODY, textColor=colors.white, fontSize=11))]]
    t = Table(data, colWidths=[160*mm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),header_color),
                           ("BOX",(0,0),(-1,-1),0.5,header_color),
                           ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
                           ("LEFTPADDING",(0,0),(-1,-1),10)]))
    story.append(t)

# ============================================================ COVER
story.append(Spacer(1, 40))
story.append(Paragraph("ScholarRAG", H1))
story.append(Paragraph("How the App Works - and How It Runs in the Cloud<br/>"
                       "A walkthrough for developers: RAG pipeline, Docker &amp; Kubernetes", SUB))
story.append(Spacer(1, 10))

intro = Table([[Paragraph("<b>What is ScholarRAG?</b><br/><br/>"
    "ScholarRAG is a research assistant. You ask a question about machine learning or "
    "computer science, and it searches a database of <b>22,000 academic papers</b>, pulls the "
    "most relevant ones, and uses Claude (an AI model) to write you a real answer - with "
    "citations and links to code on GitHub.<br/><br/>"
    "This document explains two things:<br/>"
    "1. <b>The app</b> - how a question becomes an answer (the RAG pipeline)<br/>"
    "2. <b>The cloud</b> - how we package and run it with Docker and Kubernetes", BODY)]],
    colWidths=[165*mm])
intro.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),LIGHT),
                           ("BOX",(0,0),(-1,-1),1,BLUE),("TOPPADDING",(0,0),(-1,-1),12),
                           ("BOTTOMPADDING",(0,0),(-1,-1),12),("LEFTPADDING",(0,0),(-1,-1),12),
                           ("RIGHTPADDING",(0,0),(-1,-1),12)]))
story.append(intro)
story.append(Spacer(1, 16))
story.append(Paragraph("Three pieces work together:", H3))
arch = Table([
    [Paragraph("<b>Frontend</b><br/>React + nginx<br/><font size=8>what the user sees</font>", BODY),
     Paragraph("<b>Backend</b><br/>FastAPI (Python)<br/><font size=8>the brain / RAG logic</font>", BODY),
     Paragraph("<b>Qdrant</b><br/>Vector database<br/><font size=8>the 22k papers</font>", BODY)],
], colWidths=[55*mm,55*mm,55*mm])
arch.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(0,0),colors.HexColor("#fff3e0")),
    ("BACKGROUND",(1,0),(1,0),colors.HexColor("#e8f5e9")),
    ("BACKGROUND",(2,0),(2,0),colors.HexColor("#f3e5f5")),
    ("BOX",(0,0),(0,0),1,ORANGE),("BOX",(1,0),(1,0),1,GREEN),("BOX",(2,0),(2,0),1,PURPLE),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(-1,-1),"CENTER"),
    ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
story.append(arch)
story.append(PageBreak())

# ============================================================ PART 1 - THE APP
story.append(Paragraph("Part 1 - How the App Works", H1))
story.append(Paragraph("From a typed question to a cited answer", SUB))

story.append(Paragraph("The core idea: RAG (Retrieval-Augmented Generation)", H2))
story.append(Paragraph(
    "An AI model like Claude is smart but doesn't know about your specific 22,000 papers. "
    "RAG fixes that: before asking the AI to answer, we first <b>retrieve</b> the most relevant "
    "papers and hand them to the AI as context. The AI then <b>generates</b> an answer grounded "
    "in those papers. Retrieval + Generation = RAG.", BODY))

story.append(Paragraph("But computers don't understand words - they understand numbers", H3))
story.append(Paragraph(
    "Every paper's title + abstract is converted into a list of 384 numbers called an "
    "<b>embedding</b> (a 'vector'). Papers about similar topics end up with similar numbers. "
    "When you ask a question, your question is turned into 384 numbers too - then we just find "
    "the papers whose numbers are closest. This is what Qdrant (the vector database) does, "
    "incredibly fast, across all 22k papers.", BODY))
story.append(Paragraph(
    "The model that turns text into numbers is called <font face='Courier'>all-MiniLM-L6-v2</font>. "
    "<b>Important:</b> the same model must be used when storing papers AND when searching, or the "
    "numbers won't be comparable.", NOTE))

story.append(Paragraph("The full journey of one question", H2))

steps = [
    ("1. User asks a question", GREEN,
     "e.g. \"What are efficient attention mechanisms for transformers?\" The React frontend sends "
     "it to the backend. The user must be logged in - a token proves who they are."),
    ("2. Embed the question", BLUE,
     "The backend converts the question into 384 numbers using all-MiniLM-L6-v2."),
    ("3. Search Qdrant", PURPLE,
     "Qdrant compares those numbers against all 22k papers and returns the top 8 closest matches "
     "(this is the 'bi-encoder' retrieval step)."),
    ("4. Filter &amp; pick the best 2", ORANGE,
     "We drop weak matches (similarity score below 0.35), prefer papers that have GitHub code, "
     "and keep the best 2 to use as context. Fewer, stronger papers beat many weak ones."),
    ("5. Build the prompt", GREEN,
     "The 2 papers' titles, abstracts and GitHub links are packed into a prompt, along with the "
     "system instructions that tell Claude how to behave (answer first, cite papers only if useful)."),
    ("6. Claude generates the answer", BLUE,
     "Claude writes the answer. It can even call a 'fetch_url' tool to read a GitHub README or "
     "raw code file live if it needs to explain an implementation in depth."),
    ("7. Stream back &amp; save", PURPLE,
     "The answer streams word-by-word to the screen (Server-Sent Events). The question, answer "
     "and sources are saved to SQLite so the chat history persists."),
]
for title, c, desc in steps:
    box(title, [], c)
    story.append(Spacer(1,2))
    story.append(Paragraph(desc, BODY))
    story.append(Spacer(1,4))

story.append(Paragraph("Extra abilities", H3))
bullets([
    "<b>PDF upload:</b> drop in a paper and the answer is grounded in that specific document.",
    "<b>Memory:</b> each chat remembers previous turns, so follow-up questions keep context.",
    "<b>Accounts:</b> register / login, and every user's chats are private to them.",
    "<b>Model choice:</b> the backend can call different Claude models (Haiku for speed, Sonnet for depth).",
])
story.append(PageBreak())

# ============================================================ PART 2 - DOCKER
story.append(Paragraph("Part 2 - Docker", H1))
story.append(Paragraph("Packaging each piece so it runs anywhere", SUB))

story.append(Paragraph("What problem does Docker solve?", H2))
story.append(Paragraph(
    "The backend needs Python + PyTorch. The frontend needs Node + nginx. Qdrant is its own "
    "program. Installing all of that on every machine by hand is painful and breaks easily "
    "(\"works on my machine\"). <b>Docker</b> packages each piece - code plus everything it needs "
    "to run - into a self-contained <b>image</b>. An image started up and running is a "
    "<b>container</b>. The same image runs identically on your laptop or on a cloud server.", BODY))
story.append(Paragraph(
    "Think of an image as a recipe + all ingredients sealed in a box. A container is the meal "
    "cooked from it. One recipe, many identical meals.", NOTE))

story.append(Paragraph("The Dockerfile - the recipe", H2))
story.append(Paragraph("Backend Dockerfile (Python/FastAPI):", H3))
code('FROM python:3.11-slim          # start from a small Python\n'
     'WORKDIR /app                   # work inside /app\n'
     'COPY requirements.txt .        # copy the dependency list\n'
     'RUN pip install torch ...      # install PyTorch (CPU build)\n'
     'RUN pip install -r requirements.txt\n'
     'COPY . .                       # copy the source code\n'
     'EXPOSE 8000\n'
     'CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]')
story.append(Paragraph(
    "We copy <font face='Courier'>requirements.txt</font> and install <i>before</i> copying the code. "
    "Docker caches each step - so if only the code changes, it reuses the cached install and rebuilds "
    "in seconds.", BODY))

story.append(Paragraph("Frontend Dockerfile (two stages):", H3))
code('# Stage 1 - build the React app\n'
     'FROM node:20 AS build\n'
     'WORKDIR /app\n'
     'COPY package*.json ./\n'
     'RUN npm install\n'
     'COPY . .\n'
     'ARG VITE_API_URL=/api         # API calls go to /api\n'
     'RUN npm run build             # compile to static files\n\n'
     '# Stage 2 - serve with nginx\n'
     'FROM nginx:alpine             # tiny, Node is discarded\n'
     'COPY --from=build /app/dist /usr/share/nginx/html\n'
     'COPY nginx.conf /etc/nginx/conf.d/default.conf')
story.append(Paragraph(
    "Two stages = build in a big Node container, then copy <b>only</b> the finished files into a "
    "tiny nginx container. Final image: ~27 MB instead of ~1 GB.", BODY))

story.append(Paragraph("nginx - the receptionist", H2))
story.append(Paragraph(
    "The frontend container runs nginx, which does two jobs: serve the React files to the browser, "
    "and forward API calls to the backend. Its rules:", BODY))
bullets([
    "Request to <font face='Courier'>/api/search</font> -&gt; strip <font face='Courier'>/api</font> -&gt; forward to <font face='Courier'>http://backend:8000/search</font>",
    "Any other request -&gt; serve the React app (index.html)",
])
story.append(Paragraph(
    "The name <font face='Courier'>backend</font> is not a real domain - Docker provides an internal "
    "DNS so containers can find each other by name. This also avoids CORS issues, because the browser "
    "only ever talks to one address.", BODY))

story.append(Paragraph("docker-compose - running all three together", H2))
story.append(Paragraph(
    "Writing long <font face='Courier'>docker run</font> commands for three containers is tedious. "
    "<b>docker-compose.yml</b> describes all of them in one file and starts them with one command.", BODY))
code('services:\n'
     '  qdrant:\n'
     '    image: akritiyadav/scholarrag:qdrant-v1   # 22k vectors baked in\n'
     '  backend:\n'
     '    image: akritiyadav/scholarrag:backend-v12\n'
     '    environment:\n'
     '      - QDRANT_HOST=qdrant     # find qdrant by name\n'
     '    depends_on: [qdrant]\n'
     '  frontend:\n'
     '    image: akritiyadav/scholarrag:frontend-v3\n'
     '    ports: ["80:80"]          # only the frontend is public\n'
     'volumes:\n'
     '  users_data:                 # keeps users.db across restarts')
story.append(Paragraph("Start everything:", H3))
code('docker compose up -d')
story.append(Paragraph(
    "Only port 80 (the frontend) is exposed to the internet. Backend (8000) and Qdrant (6333) have "
    "no public ports - they're reachable only inside Docker's private network. That's deliberate: "
    "the database and API should never be directly reachable from outside.", NOTE))

story.append(Paragraph("Where do the images live?", H3))
story.append(Paragraph(
    "All three images are pushed to <b>Docker Hub</b> under <font face='Courier'>akritiyadav/scholarrag</font>. "
    "A new machine doesn't need the source code - <font face='Courier'>docker compose up</font> pulls the "
    "images automatically. The Qdrant image even has all 22k paper vectors baked inside it, so there's "
    "no separate data-loading step.", BODY))
story.append(PageBreak())

# ============================================================ PART 3 - KUBERNETES
story.append(Paragraph("Part 3 - Kubernetes", H1))
story.append(Paragraph("Running it like production: self-healing &amp; scaling", SUB))

story.append(Paragraph("Why move from docker-compose to Kubernetes?", H2))
story.append(Paragraph(
    "docker-compose runs containers on one machine. If a container crashes, it may stay down. "
    "If traffic spikes, you can't easily run more copies. <b>Kubernetes (k8s)</b> manages containers "
    "for you:", BODY))
bullets([
    "<b>Self-healing</b> - a crashed container is restarted automatically.",
    "<b>Scaling</b> - run 2+ copies (replicas) of the backend, traffic is shared between them.",
    "<b>Load balancing</b> - requests spread across all healthy copies.",
    "<b>Rolling updates</b> - deploy a new version with zero downtime.",
])

story.append(Paragraph("The vocabulary (just 5 words)", H2))
vocab = Table([
    [Paragraph("<b>Pod</b>", BODY),        Paragraph("The smallest unit - a running container (e.g. one backend).", BODY)],
    [Paragraph("<b>Deployment</b>", BODY), Paragraph("Says \"keep N copies of this pod alive\" and handles updates.", BODY)],
    [Paragraph("<b>Service</b>", BODY),    Paragraph("A stable internal address for a set of pods (pods come and go, the Service name doesn't).", BODY)],
    [Paragraph("<b>Ingress</b>", BODY),    Paragraph("The front door - routes outside traffic to the right Service (like nginx.conf).", BODY)],
    [Paragraph("<b>Node</b>", BODY),       Paragraph("A machine in the cluster that runs pods.", BODY)],
], colWidths=[35*mm, 130*mm])
vocab.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,GREY),("INNERGRID",(0,0),(-1,-1),0.4,colors.lightgrey),
                           ("BACKGROUND",(0,0),(0,-1),LIGHT),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                           ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
                           ("LEFTPADDING",(0,0),(-1,-1),8)]))
story.append(vocab)
story.append(Spacer(1,8))

story.append(Paragraph("ClusterIP - the stable address", H3))
story.append(Paragraph(
    "Every pod gets an IP that changes whenever it restarts. A <b>Service</b> gives a fixed virtual "
    "IP (ClusterIP) that never changes. So the backend always reaches Qdrant at "
    "<font face='Courier'>qdrant:6333</font>, even after Qdrant restarts with a new pod IP.", BODY))

story.append(Paragraph("Our cluster runs inside kind", H2))
story.append(Paragraph(
    "We use <b>kind</b> (Kubernetes IN Docker) - it runs a whole k8s cluster inside Docker containers "
    "on a single EC2 server. <font face='Courier'>kind-config.yaml</font> sets up the nodes and, crucially, "
    "maps the server's port 8080 to the cluster's port 80 - that's how the browser gets in.", BODY))
code('Browser -&gt; EC2:8080 -&gt; kind node:80 -&gt; Ingress -&gt; Service -&gt; Pod')

story.append(Paragraph("What we deploy", H2))
deploy = Table([
    [Paragraph("<b>Component</b>", BODY), Paragraph("<b>Replicas</b>", BODY), Paragraph("<b>Service type</b>", BODY), Paragraph("<b>Notes</b>", BODY)],
    [Paragraph("frontend", BODY), Paragraph("2", BODY), Paragraph("ClusterIP", BODY), Paragraph("nginx + React", BODY)],
    [Paragraph("backend", BODY),  Paragraph("2", BODY), Paragraph("ClusterIP", BODY), Paragraph("FastAPI; /health probe; API keys from Secret", BODY)],
    [Paragraph("qdrant", BODY),   Paragraph("1", BODY), Paragraph("ClusterIP", BODY), Paragraph("vector DB", BODY)],
], colWidths=[35*mm,22*mm,32*mm,76*mm])
deploy.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,GREY),("INNERGRID",(0,0),(-1,-1),0.4,colors.lightgrey),
                            ("BACKGROUND",(0,0),(-1,0),BLUE),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),5),
                            ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),6)]))
story.append(deploy)
story.append(Spacer(1,8))
bullets([
    "<b>Rolling updates:</b> backend &amp; frontend use maxSurge=1, maxUnavailable=0 - a new pod comes up before an old one is removed, so the app never goes fully down during a deploy.",
    "<b>Secrets:</b> API keys (Anthropic, GitHub, HF) are stored in a k8s Secret, not hardcoded in the yaml.",
    "<b>readinessProbe:</b> k8s pings <font face='Courier'>/health</font>; an unhealthy pod gets no traffic.",
    "<b>hostPath volume:</b> users.db lives on the server disk, so accounts survive pod restarts.",
])

story.append(Paragraph("Ingress = the Kubernetes version of nginx.conf", H3))
story.append(Paragraph(
    "The Ingress holds the same routing rules: <font face='Courier'>/api/*</font> -&gt; backend Service, "
    "everything else -&gt; frontend Service. An <b>ingress controller</b> (nginx, installed once) is the "
    "actual software that reads those rules and routes the traffic.", BODY))

story.append(Paragraph("One gotcha we hit (worth knowing)", H3))
story.append(Paragraph(
    "The port 8080-&gt;80 mapping lives only on the <b>control-plane</b> node. By default Kubernetes may "
    "schedule the ingress controller onto a <b>worker</b> node - then traffic on 8080 never reaches it "
    "(empty reply / 404). Fix: a <font face='Courier'>nodeSelector</font> pins the ingress controller to "
    "the control-plane node. Lesson: the port mapping and the ingress controller must live on the same node.", NOTE))

story.append(Paragraph("Deploy order (and why)", H2))
code('1  kind create cluster --config kind-config.yaml\n'
     '2  kubectl apply -f ingress-controller.yaml   # install nginx controller\n'
     '3  kubectl wait ... controller ... --timeout=90s\n'
     '4  kubectl create secret ... --from-env-file=.env\n'
     '5  kubectl apply -f qdrant-deployment.yaml\n'
     '6  kubectl apply -f backend-deployment.yaml\n'
     '7  kubectl apply -f frontend-deployment.yaml\n'
     '8  kubectl apply -f ingress.yaml             # routing rules LAST')
story.append(Paragraph(
    "Steps 2 and 8 are separate on purpose: the ingress controller installs a validating webhook that "
    "checks every routing rule. If you apply the rules before the webhook is alive, they get rejected. "
    "So: install controller -&gt; wait -&gt; then apply rules.", BODY))
story.append(PageBreak())

# ============================================================ K8S DIAGRAM
story.append(Paragraph("Kubernetes - Architecture at a Glance", H1))
story.append(Paragraph("Everything inside one EC2 server", SUB))

def _rect(d,x,top,w,h,fill,stroke,dash=None,sw=1):
    r=Rect(x, top-h, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=sw)
    r.rx=4; r.ry=4
    if dash: r.strokeDashArray=dash
    d.add(r)

def _t(d,x,y,s,size=8.5,color=colors.black,anchor="middle",bold=False):
    st=String(x,y,s,fontSize=size,fillColor=color,textAnchor=anchor)
    st.fontName="Helvetica-Bold" if bold else "Helvetica"
    d.add(st)

def _arrow(d,x,y1,y2,color=colors.HexColor("#555555")):
    d.add(Line(x,y1,x,y2,strokeColor=color,strokeWidth=1.2))
    d.add(Polygon([x-3,y2+5, x+3,y2+5, x,y2],fillColor=color,strokeColor=color))

def k8s_diagram():
    W,H=468,414
    d=Drawing(W,H)
    def ty(o): return H-o
    G=colors.HexColor("#2e7d32"); Gl=colors.HexColor("#e8f5e9")
    Or=colors.HexColor("#e65100"); Ol=colors.HexColor("#fff3e0")
    Pu=colors.HexColor("#6a1b9a"); Pl=colors.HexColor("#f3e5f5")
    Bl=colors.HexColor("#1e88e5"); Bll=colors.HexColor("#e3f2fd")
    BG=colors.HexColor("#546e7a")  # blue-grey for worker nodes
    grey=colors.HexColor("#666666")

    # Browser
    _rect(d,159,ty(6),150,26,colors.HexColor("#eceff1"),grey,sw=1.2)
    _t(d,234,ty(17),"Browser",9.5,colors.black,bold=True)
    _t(d,234,ty(27),"http://<server-ip>:8080",7,grey)
    _arrow(d,234,ty(32),ty(44))

    # EC2 outer
    _rect(d,4,ty(44),460,362,colors.white,Bl,dash=(5,3),sw=1.3)
    _t(d,12,ty(56),"EC2 Instance",8,Bl,anchor="start",bold=True)

    # kind cluster
    _rect(d,14,ty(60),440,340,colors.HexColor("#fbfbff"),Pu,dash=(4,3),sw=1.3)
    _t(d,22,ty(72),"kind cluster  (1 control-plane + 2 worker nodes)",8,Pu,anchor="start",bold=True)

    # ---- CONTROL-PLANE NODE ----
    _rect(d,24,ty(80),420,80,Bll,Bl,sw=1.3)
    _t(d,32,ty(91),"control-plane node",7.6,Bl,anchor="start",bold=True)
    _rect(d,34,ty(98),400,18,colors.HexColor("#bbdefb"),Bl,sw=0.6)
    _t(d,234,ty(110),"EC2 port 8080  ->  cluster port 80   enters the cluster HERE",7.2,colors.HexColor("#0d47a1"))
    _rect(d,150,ty(120),168,34,colors.white,Bl,sw=1.4)
    _t(d,234,ty(132),"Ingress Controller (nginx)",8.3,Bl,bold=True)
    _t(d,234,ty(143),"pinned here via nodeSelector",6.6,grey)
    _arrow(d,234,ty(160),ty(174),grey)

    # ---- SERVICES BAND (cluster-wide) ----
    _rect(d,24,ty(178),420,46,colors.HexColor("#fafafa"),grey,sw=0.8)
    _t(d,32,ty(188),"Services  -  cluster-wide virtual IPs (ClusterIP), route to pods on any node",6.8,grey,anchor="start",bold=True)
    _rect(d,40,ty(196),118,24,Gl,G,sw=1.1);  _t(d,99,ty(208),"backend Svc : 8000",6.8,G,bold=True)
    _rect(d,175,ty(196),118,24,Pl,Pu,sw=1.1); _t(d,234,ty(208),"qdrant Svc : 6333",6.8,Pu,bold=True)
    _rect(d,310,ty(196),118,24,Ol,Or,sw=1.1); _t(d,369,ty(208),"frontend Svc : 80",6.8,Or,bold=True)
    # arrows down to workers
    _arrow(d,128,ty(224),ty(238),grey); _arrow(d,350,ty(224),ty(238),grey)

    # ---- WORKER NODE 1 ----
    _rect(d,24,ty(242),208,150,colors.HexColor("#f5f7f8"),BG,sw=1.3)
    _t(d,32,ty(253),"worker node 1",7.6,BG,anchor="start",bold=True)
    _rect(d,34,ty(258),188,26,Gl,G,sw=1); _t(d,128,ty(268),"backend pod 1",6.8,colors.black,bold=True); _t(d,128,ty(278),"FastAPI : 8000  |  /health",6,grey)
    _rect(d,34,ty(288),188,26,Ol,Or,sw=1); _t(d,128,ty(298),"frontend pod 1",6.8,colors.black,bold=True); _t(d,128,ty(308),"nginx + React",6,grey)
    _rect(d,34,ty(318),188,26,Pl,Pu,sw=1); _t(d,128,ty(328),"qdrant pod",6.8,colors.black,bold=True); _t(d,128,ty(338),"22k vectors baked in",6,grey)

    # ---- WORKER NODE 2 ----
    _rect(d,236,ty(242),208,150,colors.HexColor("#f5f7f8"),BG,sw=1.3)
    _t(d,244,ty(253),"worker node 2",7.6,BG,anchor="start",bold=True)
    _rect(d,246,ty(258),188,26,Gl,G,sw=1); _t(d,340,ty(268),"backend pod 2",6.8,colors.black,bold=True); _t(d,340,ty(278),"FastAPI : 8000  |  /health",6,grey)
    _rect(d,246,ty(288),188,26,Ol,Or,sw=1); _t(d,340,ty(298),"frontend pod 2",6.8,colors.black,bold=True); _t(d,340,ty(308),"nginx + React",6,grey)
    _t(d,340,ty(330),"(qdrant has 1 replica,",6,grey); _t(d,340,ty(339),"so it runs on worker 1 only)",6,grey)

    return d

story.append(k8s_diagram())
story.append(Spacer(1,6))
story.append(Paragraph("<b>The key point - node separation:</b> traffic on port 8080 only enters at the "
    "<b>control-plane node</b>, so the Ingress controller must live there too (that is the "
    "<font face='Courier'>nodeSelector</font> we added). The actual app pods are scheduled onto the "
    "<b>worker nodes</b>. The Services sit above the nodes as cluster-wide virtual IPs - they load-balance "
    "to the right pods no matter which worker those pods landed on. So the backend reaches Qdrant simply "
    "by the name <font face='Courier'>qdrant</font>, and the user never needs to know which node anything "
    "runs on. (Secrets supply the backend's API keys; a hostPath volume keeps users.db on the EC2 disk - "
    "both omitted here for clarity, shown in the deployment table earlier.)", BODY))
story.append(PageBreak())

# ============================================================ THE BIG PICTURE
story.append(Paragraph("The Whole Picture", H1))
story.append(Paragraph("One request, end to end, in Kubernetes", SUB))

flow = [
    ("Browser", "http://&lt;server-ip&gt;:8080", GREY),
    ("kind port map", "8080 -&gt; cluster port 80", PURPLE),
    ("Ingress (nginx)", "/api/* -&gt; backend  |  /* -&gt; frontend", BLUE),
    ("Service", "stable address, load-balances across pods", GREEN),
    ("Frontend pod / Backend pod", "React served | or FastAPI runs RAG", ORANGE),
    ("Backend -&gt; Qdrant", "QDRANT_HOST=qdrant : 6333, search 22k vectors", PURPLE),
    ("Backend -&gt; Claude API", "generate the final answer, stream back", RED),
]
for i,(t,d,c) in enumerate(flow):
    row = Table([[Paragraph(f"<b>{t}</b>", ParagraphStyle('x',parent=BODY,textColor=colors.white)),
                  Paragraph(d, ParagraphStyle('y',parent=BODY,textColor=colors.white,fontSize=9))]],
                colWidths=[55*mm,110*mm])
    row.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),c),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                             ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
                             ("LEFTPADDING",(0,0),(-1,-1),10)]))
    story.append(row)
    if i < len(flow)-1:
        story.append(Paragraph("<para align=center>|</para>", ParagraphStyle('a',parent=BODY,fontSize=11,textColor=GREY,spaceBefore=1,spaceAfter=1)))

story.append(Spacer(1,14))
story.append(Paragraph("Three environments, same app", H2))
envs = Table([
    [Paragraph("<b></b>", BODY), Paragraph("<b>Local dev</b>", BODY), Paragraph("<b>Docker Compose</b>", BODY), Paragraph("<b>Kubernetes</b>", BODY)],
    [Paragraph("Proxy", BODY), Paragraph("Vite", BODY), Paragraph("nginx", BODY), Paragraph("Ingress", BODY)],
    [Paragraph("Entry port", BODY), Paragraph("5173", BODY), Paragraph("80", BODY), Paragraph("8080", BODY)],
    [Paragraph("Copies of each", BODY), Paragraph("1", BODY), Paragraph("1", BODY), Paragraph("2 (backend/frontend)", BODY)],
    [Paragraph("Self-healing", BODY), Paragraph("No", BODY), Paragraph("restart policy", BODY), Paragraph("Yes", BODY)],
], colWidths=[38*mm,38*mm,45*mm,44*mm])
envs.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,GREY),("INNERGRID",(0,0),(-1,-1),0.4,colors.lightgrey),
                          ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                          ("BACKGROUND",(0,1),(0,-1),LIGHT),
                          ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),5),
                          ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)]))
story.append(envs)
story.append(Spacer(1,12))

story.append(Paragraph("Glossary", H2))
gloss = [
    "<b>Embedding / vector:</b> a list of numbers representing the meaning of text.",
    "<b>RAG:</b> Retrieval-Augmented Generation - fetch relevant docs, then let the AI answer using them.",
    "<b>Image / container:</b> a sealed package of code+deps / a running instance of it.",
    "<b>Registry (Docker Hub):</b> where images are stored and pulled from.",
    "<b>Pod / Deployment / Service / Ingress:</b> k8s building blocks (run / keep-alive / address / front door).",
    "<b>kind:</b> Kubernetes running inside Docker, for single-machine clusters.",
    "<b>Replica:</b> one of several identical copies of a pod.",
]
bullets(gloss)

story.append(Spacer(1,10))
story.append(Paragraph("<para align=center><font color='#555555' size=9>"
                       "ScholarRAG - internal architecture walkthrough</font></para>", BODY))

doc = SimpleDocTemplate("E:/proj/SchlorRag/ScholarRAG_Explained.pdf", pagesize=A4,
                        leftMargin=22*mm, rightMargin=22*mm, topMargin=20*mm, bottomMargin=18*mm,
                        title="ScholarRAG Explained", author="ScholarRAG")
doc.build(story)
print("PDF written")
