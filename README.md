# Oráculos da Sats Lottu

Lista pública das pessoas de confiança que decidem o resultado dos **mercados de previsões** da Sats Lottu.

> **Status: em preparação.** A Sats Lottu ainda não lê esta lista; o desenho está na proposta do comitê de oráculos. Entrar na lista hoje é se cadastrar com antecedência. Os mercados continuam em beta fechado.

## Como funciona

1. Quem quer ser oráculo entra nesta lista, com a **chave Nostr** (`npub`) e a prova de que controla essa chave.
2. Um mantenedor do repositório revisa e aprova a entrada.
3. Cada mercado que usa comitê **fixa uma cópia da lista** na hora em que é criado. Quem entra ou sai depois não muda um mercado em andamento.
4. Depois do fechamento do mercado, cada oráculo do comitê **assina o resultado** com a própria chave Nostr, com um link de evidência.
5. Quando a **maioria do comitê** assina o mesmo resultado, ele vira a proposta de resolução do mercado, que segue para a janela de contestação e a liquidação.

As assinaturas são públicas e qualquer pessoa pode conferi-las. Ninguém precisa de senha ou conta para ser oráculo: a chave Nostr é a identidade.

## Como virar oráculo

Veja o passo a passo em [CONTRIBUTING.md](CONTRIBUTING.md). Em resumo: você assina uma mensagem com a sua chave Nostr dizendo quem é no GitHub, gera a sua linha com `scripts/make_entry.py` e abre uma pull request. Uma verificação automática confere a assinatura antes de um mantenedor olhar.

## Regras

- **Uma entrada por pessoa**, com a própria chave e o próprio usuário do GitHub.
- **Conflito de interesse:** não decida um mercado em que você apostou, nem um que você criou. As assinaturas são públicas e a contestação existe para isso.
- **Evidência:** cada assinatura deve trazer um link da fonte que sustenta o resultado.
- **Só o resultado que a fonte mostra:** nada de opinião. Em dúvida real, o resultado correto é "anular", e o mercado é reembolsado.
- Quem sai da lista abre uma pull request removendo a própria entrada. Mantenedores podem remover entradas que violem estas regras.

## Incentivo

Os oráculos recebem **10% da taxa** do mercado, dividida igualmente entre quem assinou o resultado final **e** informou a evidência. Quem assinou outro resultado, quem não assinou e quem não apresentou evidência não recebe. O pagamento só acontece depois da contestação e da liquidação, e não há pagamento se o mercado for anulado.

Para receber, o oráculo precisa de uma conta da Sats Lottu com a chave Nostr ligada. Em mercados pequenos o valor é pequeno.

## Quem aprova

Quem mantém este repositório aprova as pull requests. O mantenedor confere se:

- a verificação automática passou;
- a pessoa é identificável e tem um histórico público que sustenta a confiança;
- não há sinal de várias entradas da mesma pessoa.

## Formato do `oracles.json`

```json
{
  "version": 1,
  "oracles": [
    {
      "npub": "npub1...",
      "github": "usuario",
      "added": "2026-11-06",
      "name": "Nome (opcional)",
      "links": ["https://exemplo.com/voce"],
      "proof": { "...": "evento Nostr assinado, gerado como no CONTRIBUTING.md" }
    }
  ]
}
```

| Campo | Obrigatório | Regra |
|---|---|---|
| `npub` | sim | chave pública no formato `npub1...` |
| `github` | sim | usuário do GitHub de quem pede a entrada |
| `added` | sim | data no formato `AAAA-MM-DD` |
| `proof` | sim | evento Nostr assinado pela chave (kind 30078) com as tags `d`, `repo` e `github` |
| `name` | não | até 60 caracteres |
| `links` | não | até 5 endereços `https://` |

A prova de posse impede que alguém cadastre a chave de outra pessoa: o evento assinado nomeia o usuário do GitHub e este repositório, e só quem tem a chave consegue produzi-lo.

## Verificação automática

`scripts/verify.py` valida o arquivo e confere cada prova (assinatura BIP-340, sem dependências além do Python). Em pull requests ele também exige que **só as entradas que o autor adicionou ou alterou** pertençam a ele. Para rodar localmente:

```bash
python scripts/verify.py oracles.json
python -m unittest discover -s tests
```

## Configuração recomendada do repositório

Estas regras ficam no GitHub, em *Settings › Branches*, para a branch `main`, e não nos arquivos:

- exigir pull request antes de mesclar, com **pelo menos 1 aprovação** (2 quando houver mais de um mantenedor);
- exigir que a verificação `verify` passe;
- exigir revisão dos donos do código (`.github/CODEOWNERS`);
- bloquear push forçado e apagar a branch;
- opcional: exigir commits assinados.

Quem controla a aprovação controla quem pode decidir os mercados. Por isso o histórico fica público e cada mercado guarda a sua própria cópia da lista.
