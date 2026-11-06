# Oráculos da Sats Lottu

Lista pública das pessoas de confiança que decidem o resultado dos **mercados de previsões** da Sats Lottu.

> **Status: em preparação.** A Sats Lottu ainda não lê esta lista; o desenho está na proposta do comitê de oráculos. Entrar na lista hoje é se cadastrar com antecedência. Os mercados continuam em beta fechado.

## Como funciona

1. Quem mantém o repositório coloca nesta lista as **chaves Nostr** (`npub`) de pessoas de confiança. Não é preciso GitHub, prova nem cadastro da pessoa.
2. Quem quiser pedir a entrada por conta própria também pode, com uma prova assinada (veja abaixo), e o mantenedor revisa.
3. Cada mercado que usa comitê **fixa uma cópia da lista** na hora em que é criado. Quem entra ou sai depois não muda um mercado em andamento.
4. Depois do fechamento do mercado, cada oráculo do comitê **assina o resultado** com a própria chave Nostr, com um link de evidência.
5. Quando a **maioria do comitê** assina o mesmo resultado, ele vira a proposta de resolução do mercado, que segue para a janela de contestação e a liquidação.

As assinaturas são públicas e qualquer pessoa pode conferi-las. Ninguém precisa de senha ou conta para ser oráculo: a chave Nostr é a identidade.

## Como virar oráculo

Há dois caminhos, descritos em [CONTRIBUTING.md](CONTRIBUTING.md):

- **Convite do mantenedor** (o mais simples): o mantenedor adiciona a sua `npub` com `python scripts/add_npub.py npub1... --name "Nome"`. Você não faz nada.
- **Pedido seu**: você assina uma mensagem com a sua chave Nostr dizendo quem é no GitHub, gera a sua linha com `scripts/make_entry.py` e abre uma pull request. Uma verificação automática confere a assinatura antes de o mantenedor olhar.

## Regras

- **Uma chave por pessoa.** Quem pede por conta própria tem uma entrada por usuário do GitHub; no convite, o mantenedor garante que não há duas chaves da mesma pessoa.
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
- não há sinal de várias entradas da mesma pessoa;
- só os mantenedores (campo `maintainers`) adicionam entradas sem prova.

## Formato do `oracles.json`

```json
{
  "version": 1,
  "maintainers": ["usuario-do-github-do-mantenedor"],
  "oracles": [
    { "npub": "npub1...", "added": "2026-11-06", "name": "Convidado pelo mantenedor" },
    {
      "npub": "npub1...",
      "added": "2026-11-06",
      "github": "usuario",
      "proof": { "...": "evento Nostr assinado, gerado como no CONTRIBUTING.md" },
      "name": "Quem pediu por conta própria",
      "links": ["https://exemplo.com/voce"]
    }
  ]
}
```

| Campo | Obrigatório | Regra |
|---|---|---|
| `npub` | sim | chave pública no formato `npub1...` |
| `added` | sim | data no formato `AAAA-MM-DD` |
| `github` e `proof` | juntos, ou nenhum | só para quem pede por conta própria: usuário do GitHub e evento Nostr assinado pela chave (kind 30078) com as tags `d`, `repo` e `github` |
| `name` | não | até 60 caracteres |
| `links` | não | até 5 endereços `https://` |

A prova de posse impede que **um estranho** cadastre a chave de outra pessoa: o evento assinado nomeia o usuário do GitHub e este repositório, e só quem tem a chave consegue produzi-lo. Entradas sem prova só valem se vierem de um mantenedor, e a lista de mantenedores que conta é a da branch de destino, não a da própria pull request.

## Verificação automática

`scripts/verify.py` valida o arquivo e confere cada prova (assinatura BIP-340, sem dependências além do Python). Em pull requests ele também exige que cada entrada adicionada ou alterada venha de quem pode: o dono da prova (usuário do GitHub) ou um mantenedor. Para rodar localmente:

```bash
python scripts/verify.py oracles.json
python -m unittest discover -s tests
```

## Configuração do repositório

Estas regras ficam no GitHub, em *Settings › Branches*, na branch `main`, e não nos arquivos. Hoje estão assim:

- a verificação `verify` precisa passar antes de qualquer mudança entrar;
- push forçado e exclusão da branch estão bloqueados, então o histórico da lista não é reescrito;
- **não se exige aprovação**, porque há um só mantenedor. A aprovação é por convenção: quem mantém o repositório revisa e mescla as pull requests;
- as regras não valem para quem administra o repositório.

Quando houver um segundo mantenedor, o passo seguinte é exigir **pelo menos 1 aprovação** e a revisão dos donos do código (`.github/CODEOWNERS`), e opcionalmente commits assinados.

Quem controla a aprovação controla quem pode decidir os mercados. Por isso o histórico fica público e cada mercado guarda a sua própria cópia da lista.
