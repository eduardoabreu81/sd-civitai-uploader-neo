# Project Context Handoff — CivitAI Uploader Neo

> Internal handoff document. Mantém o contexto técnico e histórico do projeto em um único lugar. **Nunca commit.**

---

## 1. Visão Geral

**CivitAI Uploader Neo** — Extensão para Stable Diffusion WebUI Forge Neo que permite navegar, comparar e fazer upload de imagens geradas localmente para o CivitAI via o MCP server oficial (`https://mcp.civitai.com/mcp`).

- **Name:** CivitAI Uploader Neo
- **Version:** v0.1.0
- **Repo:** https://github.com/eduardoabreu81/sd-civitai-uploader-neo
- **Stack:** Python 3.x, Gradio 4.40.0+, Vanilla JS, Sortable.js
- **Host:** Stable Diffusion WebUI Forge Neo

---

## 2. Estado Atual (v0.1.0)

Extensão funcional com upload real validado:
- Navegação de pastas locais com subpastas.
- Preview, metadados de geração e comparação lado a lado.
- Seleção múltipla com Ctrl/Cmd/Shift e reordenação drag-and-drop.
- Upload direto para CivitAI via MCP (`upload_image` → `create_post`).
- Limite de 20 imagens por post e 10 MB por imagem.
- Badge de usuário no topo da aba (`whoami` → `👤 username`).

**Limitação conhecida:** o MCP **não extrai metadados de geração** automaticamente. A solução será colocar os metadados formatados no campo `detail` e associar o checkpoint via `modelVersionId`.

---

## 3. Invariantes que Não Podem Ser Quebrados

1. **Gradio 4+ only.** Nunca usar APIs do Gradio 3.
2. **20 imagens por post.** Limite do CivitAI; aplicar no JS e no Python.
3. **10 MB por imagem.** CivitAI MCP rejeita imagens maiores; converter para PNG e oferecer resize.
4. **API key nunca logada.** Ler apenas de `opts.civitai_gallery_api_key`.
5. **Nunca commitar artefatos de runtime:** `config_states/`, `docs/`, `AGENTS.local.md`, `__pycache__/`.
6. **MCP schemas são autoritativos.** Validar contra o server real antes de mudar lógica de upload/post.
7. **Não expor NSFW/scheduling na UI** — o MCP `create_post` atual não suporta.
8. **Manter compatibilidade sem Browser Neo.** A extensão deve funcionar sozinha, mas pode aproveitar o cache do Browser Neo quando disponível.

---

## 4. Arquitetura Principal

```
Forge Neo
└── CivitAI Gallery tab (Gradio 4)
    ├── javascript/civitai-gallery.js
    │   └── Seleção, preview, favoritos, drag-drop, sync com Gradio
    ├── scripts/civitai_gallery_gui.py
    │   └── UI Gradio, callbacks, renderização HTML
    ├── scripts/civitai_gallery_utils.py
    │   └── Scan de pastas, thumbnails, filtros
    ├── scripts/civitai_gallery_meta.py
    │   └── Extração de metadados PNG e diff
    ├── scripts/civitai_gallery_tags.py
    │   └── Tags/favoritos locais
    ├── scripts/civitai_gallery_api.py
    │   └── Cliente JSON-RPC para o MCP da CivitAI
    └── (planned) scripts/civitai_gallery_model_resolver.py
        └── Resolve modelVersionId a partir do metadata da imagem
```

### Fluxo de Upload

1. Usuário seleciona imagens na galeria.
2. Clica em **Auto-fill** ou preenche título/desc/tags manualmente.
3. Clica em **Post**.
4. Backend chama `whoami()` para validar conta.
5. Para cada imagem:
   - `upload_image(path)` converte para PNG base64 e envia.
   - Recebe `uuid` da imagem.
6. Backend chama `create_post(title, detail, images[].uuid, tags, modelVersionId?, publish)`.
7. Retorna URL do post/rascunho.

---

## 5. Descobertas Importantes sobre o MCP

### `upload_image`
- Aceita `url` ou `data` (base64) + `contentType` opcional.
- Retorna `uuid` e dimensões.
- **Não extrai metadados de geração do PNG.**

### `create_post`
- Aceita: `title`, `detail`, `images[]`, `tags[]`, `modelVersionId`, `collectionId`, `publish`.
- **Não aceita metadados estruturados** (prompt, sampler, seed, resources).
- `modelVersionId` associa o post a uma versão de modelo e funciona corretamente.

### `whoami`
- Retorna `username`, `isOnboarded`, `completedSteps`, `muted`, etc.
- Usado para badge de usuário e validação antes de postar.

---

## 6. Resolução de `modelVersionId` (Planejado)

Estratégia híbrida:
1. Extrair `Model:` do metadata da imagem.
2. Localizar o arquivo do checkpoint em `models/Stable-diffusion/`.
3. **Tentar cache do Browser Neo** primeiro:
   - Arquivo: `extensions/sd-civitai-browser-neo/lib/models/checkpoint_hashes.json`
   - Mapeia `caminho_do_arquivo → {sha256, modelId, modelVersionId}`.
4. **Fallback:** calcular SHA256 do arquivo e consultar:
   - `GET https://civitai.com/api/v1/model-versions/by-hash/{sha256}`
5. **Cache local** da extensão para evitar re-hash de arquivos grandes.

---

## 7. Pontos Sensíveis

- **JS depende de `gradioApp().querySelector(...)`** para sincronizar inputs hidden. Mudanças no DOM do Gradio podem quebrar.
- **Preview on hover** dispara callbacks Python; debounce de 150 ms.
- **Favorite toggle** re-renderiza o browser HTML e depende de `MutationObserver` para restaurar visuais de seleção.
- **Sortable.js** é inicializado lazy quando a lista de selecionados aparece no DOM.
- **Upload de checkpoints grandes:** SHA256 de ~7 GB demora ~6s. Cache é essencial.

---

## 8. Como Trabalhar no Projeto

- Ler `README.md`, `AGENTS.md`, `docs/PROJECT_CONTEXT.md` e `docs/PROJECT_LOG.md` antes de alterar comportamento.
- Preferir mudanças pequenas e localizadas.
- Validar uploads com uma chave de API real em modo rascunho.
- Nunca commitar `docs/` nem `AGENTS.local.md`.

---

## 9. Ordem Recomendada para Próximos Passos

1. ✅ Upload real validado com MCP.
2. ✅ Badge de usuário (`whoami`) adicionado.
3. 🚧 Implementar `civitai_gallery_model_resolver.py`.
4. 🚧 Integrar `modelVersionId` no `create_post`.
5. 🚧 Formatar e injetar metadados de geração no `detail`.
6. Testar fluxo completo dentro do Forge Neo.
7. Corrigir problemas específicos do Gradio 4 conforme feedback.
