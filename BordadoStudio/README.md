# 🧵 BordadoStudio

**Software livre de digitalização de bordado** — desenhe formas, gere pontos
automaticamente, importe e exporte arquivos para máquinas de bordar.

Criado do zero. **Sem login, sem ativação, sem assinatura, sem limitações.**
Instalou, usou.

![Tela do BordadoStudio](docs/preview_tela.png)

![Visualização 3D dos pontos](docs/preview_3d.png)

![Relatório de produção](docs/preview_relatorio.png)

---

## ✨ Recursos

- 🎨 **Editor de desenhos** com 6 ferramentas:
  - **Preenchimento** (tatami) — formas fechadas preenchidas com pontos
  - **Linha** — desenho livre em linha simples
  - **Retângulo** e **Elipse** — arraste para criar
  - **Satin** — colunas em zig-zag (texto, contornos, hastes)
  - 🔤 **Texto** — digite palavras em letras de bordado
- 🔤 **Módulo de Letras**: alfabeto completo (A-Z, a-z, números, pontuação
  e acentos do português: ç, ã, õ, á, é, í, ó, ú, â, ê, ô...) em 5 estilos
  (linha, satin, haste, cadeia, ponto atrás), com altura e espaçamento
- ✂️ **Transformar objetos**: espelhar (H/V), girar 90°, escalar (menu Objeto)
- ✨ **11 tipos de costura** — clique no objeto e troque em Propriedades:
  - Preenchimento (tatami), Linha simples, Bordado satin (coluna e borda)
  - ✝️ **Ponto cruz** — grade de X dentro das formas
  - ⛓️ **Cadeia** (chain) — visual de bordado à mão
  - 🪡 **Ponto atrás** — costura manual sobreposta
  - 🌿 **Ponto haste** (stem) — trança inclinada
  - ✨ **Lantejoula** — motivo circular bordado
  - ✦ Motivo cruz e ★ Motivo estrela — preenchimentos decorativos
  - 🩹 **Aplique** — posicionamento + fixação + borda (máquina)
- 🧵 **Paletas de linha** nomeadas em português + cores personalizadas
- 📐 **Propriedades ajustáveis**: espaçamento, ângulo, comprimento do ponto,
  largura e densidade do satin — com atualização imediata
- ✂️ **Edição de vértices**: arraste os quadradinhos brancos para refinar
  qualquer forma
- 💾 **Importar** arquivos DST, PES, PEC, EXP, JEF, VP3, XXX, SEW, HUS e mais
- 💽 **Exportar** para DST, PES, PEC, EXP, JEF, VP3, XXX, U01, TBF, SVG, CSV, PNG
- ▶️ **Simulação de costura** animada antes de mandar para a máquina
- 👁️ **Visualização 3D** (F6) — pontos com volume realista
- 📊 **Relatório de produção** — pontos, área, linha, tempo e custo,
  com exportação em .txt (Arquivo → Relatório de produção)
- ↩️ **Desfazer/refazer** ilimitado
- 📁 **Projetos `.bds`** — salve e continue depois
- 🔢 Barra de status com coordenadas em mm, zoom e contagem de pontos

## 🖥️ Instalação (Windows)

1. **Instale o Python** (se ainda não tiver):
   - Baixe em <https://www.python.org/downloads/>
   - ⚠️ Na instalação, **marque a opção "Add Python to PATH"**

2. **Instale o BordadoStudio**:
   - Clique duas vezes em **`instalar.bat`**
   - Pronto! O instalador cria tudo automaticamente (sem login de nada).

3. **Para usar**:
   - Clique duas vezes em **`Abrir BordadoStudio.bat`** (criado pelo instalador)

## 🚀 Como usar — manual rápido

| Ferramenta | Atalho | Como funciona |
|---|---|---|
| Selecionar | `S` | Clique no objeto para mover; arraste os quadradinhos brancos para ajustar os pontos |
| Preenchimento | `P` | Clique nos vértices da forma; **duplo-clique** termina |
| Linha | `L` | Desenhe à mão livre |
| Retângulo | `R` | Arraste na tela |
| Elipse | `E` | Arraste na tela |
| Satin | `B` | Clique ao longo do centro da faixa; duplo-clique termina |
| Texto | `T` | Clique na tela e digite o texto em letras de bordado |

**Menu Objeto:** `Ctrl+H` espelha · `Ctrl+Shift+H` espelha na vertical ·
`Ctrl+R` gira 90° · `Ctrl+M` escala

**Outros atalhos:** `Ctrl+Z` desfazer · `Ctrl+Y` refazer · `Ctrl+S` salvar ·
`Ctrl+E` exportar · `Ctrl+I` importar · `F5` simular · `F6` visualização 3D ·
`F1` ajuda · `Ctrl+H` espelhar · `Ctrl+R` girar · `Ctrl+M` escalar ·
`Espaço`+arrastar move a tela · roda do mouse = zoom · `Esc` cancela ·
`Enter` termina a forma · `Backspace` remove o último ponto

### Fluxo típico

1. Desenhe (ou importe) os objetos do seu bordado
2. Ajuste cores e densidades no painel **Propriedades**
3. Veja a costura acontecer em **Simular costura** (F5)
4. **Exportar para máquina** (Ctrl+E) e copie o arquivo para o pendrive

## 📦 Formatos de arquivo

| Formato | Importar | Exportar | Observação |
|---|---|---|---|
| DST (Tajima) | ✅ | ✅ | mais compatível; não guarda cores |
| PES / PEC (Brother) | ✅ | ✅ | cores aproximadas para a paleta Brother |
| EXP (Melco) | ✅ | ✅ | não guarda cores |
| JEF (Janome) | ✅ | ✅ | cores aproximadas |
| VP3 (Pfaff) | ✅ | ✅ | guarda cores exatas |
| XXX (Singer), U01 (Barudan), TBF | ✅ | ✅ | |
| SEW, HUS, SHV e outros | ✅ | — | apenas leitura |
| SVG, PNG, CSV | — | ✅ | visualização / análise |

## 🗂️ Exemplos

A pasta `exemplos/` contém:

- `jardim.bds` / `jardim.dst` — projeto completo (flor com 10 objetos)
- `efeitos.bds` / `efeitos.dst` — **todos os 10 tipos de costura** lado a lado

Abra os `.bds` no programa para estudar como foram feitos.

## ❓ Perguntas frequentes

**O programa pede login ou chave?**
Não. O BordadoStudio não tem login, ativação nem verificação de licença.

**Posso usar comercialmente?**
Sim. O programa é seu para usar como quiser.

**Minha máquina não lê o arquivo exportado?**
Exporte em **DST** — é o formato mais compatível. Se a sua máquina usa
pendrive, copie o arquivo para a raiz do pendrive.

**Os pontos importados podem ser editados?**
Objetos importados podem ser movidos e recoloridos. Para editar a geometria,
desenhe novamente com as ferramentas (ou peça um ajuste!).

**As lantejoulas são gravadas para máquina com ejetor de lantejoula?**
Na versão atual a lantejoula é um **motivo bordado** (círculo com ponto de
fixação) — funciona em qualquer máquina de bordar. Comandos de ejetor físico
de lantejoula são específicos de cada fabricante e podem vir em versões
futuras.

## 🛠️ Desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# testes do núcleo
python -m unittest tests.test_core -v

# teste da interface (sem abrir janela)
python tests/smoke_gui.py
```

Estrutura:

```
BordadoStudio/
├── main.py               # inicia o programa
├── instalar.bat          # instalador Windows
├── requirements.txt      # dependências (PySide6, pyembroidery)
├── bordadostudio/
│   ├── app.py            # ponto de entrada
│   ├── main_window.py    # janela principal, menus, diálogos
│   ├── canvas.py         # cena de edição e ferramentas
│   ├── stitcher.py       # geração de pontos (fill, run, satin)
│   ├── model.py          # documento, objetos, desfazer
│   ├── formats_io.py     # importar/exportar formatos de máquina
│   ├── threads.py        # paletas de linha
│   ├── simulator.py      # simulação de costura
│   ├── props_panel.py    # painel de propriedades
│   └── object_list.py    # lista de objetos
├── tests/                # testes automatizados
└── exemplos/             # projeto de exemplo
```

> **Nota sobre PySide6:** usamos `PySide6>=6.6,<6.12` porque a versão 6.12.0
> possui um bug de memória no QPainterPath (corrupção ao destruir traços
> grandes). A limitação será removida quando o bug for corrigido upstream.

---

Feito com 💛 para quem quer bordar sem depender de ninguém.
