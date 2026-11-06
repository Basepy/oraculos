# Como virar oráculo

Você precisa de uma **chave Nostr** e de uma extensão de navegador que assine eventos (NIP-07), como Alby ou nos2x. Nenhum passo pede a sua chave privada: quem assina é a extensão.

## 1. Assine a sua prova

Abra qualquer página no navegador com a extensão instalada, abra o console do navegador (F12) e rode o código abaixo, trocando `SEU_USUARIO_DO_GITHUB`. **Leia o código antes de colar**: ele só pede à extensão que assine um evento e mostra o resultado. Nunca cole no console um código que você não entenda.

```js
const proof = await window.nostr.signEvent({
  kind: 30078,
  created_at: Math.floor(Date.now() / 1000),
  tags: [
    ["d", "satslottu-oracle-registration"],
    ["repo", "Basepy/oraculos"],
    ["github", "SEU_USUARIO_DO_GITHUB"],
  ],
  content: "Quero ser oráculo da Sats Lottu",
});
console.log(JSON.stringify(proof));
```

A extensão mostra o evento e pede a sua confirmação. Copie o JSON que aparece no console e salve em um arquivo `proof.json`. Qualquer outro cliente Nostr que assine um evento com exatamente esses campos também serve.

## 2. Gere a sua linha da lista

Com o Python 3 instalado, na pasta do repositório:

```bash
python scripts/make_entry.py proof.json --name "Seu nome"
```

O script confere a assinatura e imprime a entrada pronta, com o `npub` já convertido. Use `--link https://...` para acrescentar endereços sobre você (até 5, opcional).

## 3. Abra a pull request

1. Faça um fork deste repositório.
2. Cole a entrada impressa dentro da lista `oracles` do arquivo `oracles.json`.
3. Rode `python scripts/verify.py oracles.json` para conferir.
4. Abra a pull request. A verificação automática roda sozinha.

A verificação falha se a prova não for sua, se o usuário do GitHub da prova for outro que o autor da pull request, se a entrada estiver mal formatada ou repetida, ou se você alterar a entrada de outra pessoa.

## 4. Revisão

Um mantenedor revisa e, se aprovar, mescla. Pode pedir mais informações sobre quem você é.

## Depois de entrar

Para receber o incentivo quando a Sats Lottu passar a usar a lista, ligue a sua chave Nostr a uma conta da Sats Lottu. Esse passo ainda não existe; avisaremos aqui.

## Para sair

Abra uma pull request removendo a sua entrada.
