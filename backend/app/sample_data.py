from .models import CodeEdge, CodeNode, GraphPayload


def get_sample_graph() -> GraphPayload:
    """Return a static pre-computed Python + TypeScript sample graph (no network, no parsing)."""
    nodes = [
        CodeNode(
            id="backend/auth.py",
            label="auth.py",
            kind="file",
            path="backend/auth.py",
            summary="Handles JWT token validation and session guards.",
            risk_level="high",
        ),
        CodeNode(
            id="backend/billing.py",
            label="billing.py",
            kind="file",
            path="backend/billing.py",
            summary="Processes subscription charges and invoice records.",
            risk_level="high",
        ),
        CodeNode(
            id="backend/routes.py",
            label="routes.py",
            kind="file",
            path="backend/routes.py",
            summary="FastAPI route handlers wired to auth and billing.",
            risk_level="medium",
        ),
        CodeNode(
            id="frontend/apiClient.ts",
            label="apiClient.ts",
            kind="file",
            path="frontend/apiClient.ts",
            summary="Typed HTTP client calling backend endpoints.",
            risk_level="medium",
        ),
        CodeNode(
            id="frontend/CheckoutView.tsx",
            label="CheckoutView.tsx",
            kind="file",
            path="frontend/CheckoutView.tsx",
            summary="Checkout UI component triggering payment requests.",
            risk_level="low",
        ),
    ]

    edges = [
        CodeEdge(source="backend/routes.py", target="backend/auth.py", relation="imports"),
        CodeEdge(source="backend/routes.py", target="backend/billing.py", relation="imports"),
        CodeEdge(source="frontend/apiClient.ts", target="backend/routes.py", relation="calls"),
        CodeEdge(source="frontend/CheckoutView.tsx", target="frontend/apiClient.ts", relation="imports"),
    ]

    return GraphPayload(
        source_type="sample",
        repo_name="sample/shopcore-py-ts",
        truncated=False,
        truncation_notice=None,
        nodes=nodes,
        edges=edges,
        cycles=[],
    )
