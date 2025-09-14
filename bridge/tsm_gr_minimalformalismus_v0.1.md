# TSM↔GR Minimalformalismus (v0.1)


**Kernidee:** Verwende *eine* skalierfreie, rangbasierte Größe \(B\) als gemeinsame „Bindungs‑Intensität“.
Damit lesen TSM und eine geometrische/physikalische Darstellung dieselbe Melodie in einer Notation.


## 1) Daten \(\to\) Resonanzgrößen
Gegeben Spalten \(C, \Delta\varphi, \tau\). Definiere (ε in **Grad**):
\[
F_{\mathrm{res}} \;=\; \frac{C}{\max(\Delta\varphi,\;\varepsilon_\mathrm{rad})}\cdot\tau, \quad
\varepsilon_\mathrm{rad}=\varepsilon\cdot\pi/180.
\]
**Cap:** \(\;F_{\mathrm{cap}}=\min\big(F_{\mathrm{res}},\;Q_{q}(F_{\mathrm{res}})\big)\), mit \(q=\texttt{cap\_quantile}\).


**Rang‑Mapping (skalierfrei):**
\[
B \;=\; \mathrm{ECDF}(F_{\mathrm{cap}}), \qquad S \;=\; 1-B.
\]


## 2) Zonisierung
Schwellen auf \(B\):
\(\;B\le B_\mathrm{lo}\Rightarrow\) **fragmentiert**,
\(B_\mathrm{lo}<B\le B_\mathrm{hi}\Rightarrow\) **regulativ**,
\(B>B_\mathrm{hi}\Rightarrow\) **kohärent**.
**Defaults:** \(B_\mathrm{lo}=0.2,\;B_\mathrm{hi}=0.8\).


> *Bemerkung:* Diese Definition reproduziert auf dem 100×100‑Feld exakt die beobachteten Grenzen \(F_{\mathrm{cap}}\in[0.0802,\,0.3526]\) für die \(B\)‑Schwellen bei \(q=0.99\).


## 3) Gemeinsame Sprache für Dynamik (Skizze)
- **t‑Teil (reversibel):** gewohnte Bewegung/Geodäsie auf \(M\).
- **\(\tau\)‑Teil (resonant):** Gradientenfluss in einem Potential \(K\) mit \(K\propto B\) oder \(K=\Phi(B,S,\varphi)\).
- **Zonen‑Hysterese (optional):** Mindest‑Verweilzeit \(N_\mathrm{dwell}\) + Schwell‑Puffer \(h_K\) um Oszillation an Grenzen zu dämpfen.


**Zwei Lesarten:**
1. *Metrik‑Modus:* \(\delta g_{\mu\nu}=\alpha_1 K\,g_{\mu\nu}+\alpha_2\nabla_\mu K\nabla_\nu K+\alpha_3\nabla_\mu\varphi\nabla_\nu\varphi\).
2. *Materie‑Modus:* \(T_{\mu\nu}^{(\mathrm{eff})}=T_{\mu\nu}^{(\mathrm{eff})}(K,\varphi,\nabla K,\nabla\varphi)\).


Beide verwenden **dieselben Datenobjekte** \(F_{\mathrm{cap}},B,S,\varphi\) und sind daher austauschbar dokumentier‑/prüfbar.