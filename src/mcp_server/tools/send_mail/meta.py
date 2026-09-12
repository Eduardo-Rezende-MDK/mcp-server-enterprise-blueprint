"""Metadados e heurísticas semânticas para a MCP Tool 'send_mail'."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "send_mail",
    "description": "Envia e-mails transacionais com Bearer Tokens de acesso e snippets de configuração via Gmail.",
    "documentation": DocumentationDefinition(
        summary="Dispara e-mails formatados em HTML e texto puro via Gmail (ou mock seguro em ambiente local) entregando credenciais de acesso aos usuários e leads cadastrados.",
        usageGuidelines="Invoque esta ferramenta quando o usuário solicitar o envio de tokens por e-mail, entrega de credenciais MCP ou notificações transacionais de acesso.",
        examples=[
            ExampleDefinition(
                scenario="Enviar chave de acesso recém-gerada para o e-mail do lead",
                input={
                    "to_email": "eduardo@empresa.com",
                    "recipient_name": "Eduardo Rezende",
                    "token": "mcp_live_e8471b045e758763118cfbf5ec94a02c",
                },
                expectedOutput={
                    "success": True,
                    "message": "E-mail transacional enviado com sucesso via Gmail para 'eduardo@empresa.com'.",
                    "delivery_mode": "gmail_smtp",
                },
            )
        ],
    ),
}
