# Controle do BordadoStudio (só você, Bruno, mexe aqui)

Este arquivo é o **interruptor remoto** do BordadoStudio. Cada instalação
consulta `controle/bloqueio.json` ao abrir o programa (quando há internet).

## Como bloquear / liberar

Edite `bloqueio.json` pelo celular (app GitHub) ou pelo navegador
(clique no lápis ✏️ em <https://github.com/brunocassetari1981-ctrl/STUDIO>,
pasta `controle`) e clique em **Commit changes**.

```json
{
  "bloquear": true,
  "motivo": "Licença não paga. Contate o suporte.",
  "bloquear_ids": ["abc123def456"],
  "permitir_ids": []
}
```

| Campo | Efeito |
|---|---|
| `"bloquear": true` | **Bloqueia todas** as instalações |
| `"bloquear": false` | Libera todas (exceto as da lista `bloquear_ids`) |
| `"bloquear_ids"` | Bloqueia **só essas** instalações (o ID vem no e-mail de cada instalação) |
| `"permitir_ids"` | Libera essas instalações **mesmo** com `"bloquear": true` |
| `"motivo"` | Mensagem que aparece na tela do usuário bloqueado |

## Notificações de instalação

A cada instalação você recebe um aviso em **brunocassetari@hotmail.com**
(via ntfy.sh, com cópia por e-mail) contendo: ID da instalação, nome do
computador, sistema, versão e data. Use o ID para bloquear uma máquina
específica adicionando-o em `bloquear_ids`.

- **FormSubmit (reforço):** na primeira vez, o FormSubmit manda um e-mail
  de *ativação* para o seu Hotmail — clique no link uma vez para passar a
  receber também por lá (opcional; o ntfy já entrega sozinho).
- Para testar o recebimento, reinstale o BordadoStudio e veja o e-mail.

## Detalhes técnicos

- O programa **funciona offline**: se não conseguir consultar o bloqueio,
  simplesmente abre normalmente (falha aberta).
- O bloqueio vale para quem estiver com internet; é um controle comercial,
  não uma proteção absoluta.
- Nenhum dado de bordado é enviado — só os dados de instalação listados acima.
