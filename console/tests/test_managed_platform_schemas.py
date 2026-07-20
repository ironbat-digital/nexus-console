"""Validation for the managed-platform contract schemas (v1alpha1 + v1alpha2) and docs.

These contracts are TARGET-STATE design artifacts (no Hub/Operator/Registry
code exists yet). v1alpha2 ADDS the Personal + Hub product layer (editions,
entitlements, subscriptions, organizations, package access) on top of the
v1alpha1 managed-platform infrastructure contracts; it reuses v1alpha1 crypto/
identifier primitives by absolute $id and does not break them. This test guards
so the docs cannot silently rot:

1. Every schema in docs/schemas/{v1alpha1,v1alpha2} is a valid JSON Schema 2020-12.
2. Every example fixture validates against the schema declared in
   docs/schemas/examples/index.json.
3. Every NEGATIVE fixture in examples/invalid/ is rejected by its schema.
4. No example fixture leaks a plaintext secret value.
5. Signature-envelope shape and critical product invariants hold (edition/
   entitlement/subscription/package-access/deployment-modality).
6. Every relative Markdown link under docs/ resolves to a file that exists.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_ROOT = REPO_ROOT / "docs" / "schemas"
SCHEMA_DIR = SCHEMAS_ROOT / "v1alpha1"
SCHEMA_DIR_V2 = SCHEMAS_ROOT / "v1alpha2"
SCHEMA_DIRS = {"v1alpha1": SCHEMA_DIR, "v1alpha2": SCHEMA_DIR_V2}
EXAMPLE_DIR = SCHEMAS_ROOT / "examples"
INVALID_DIR = EXAMPLE_DIR / "invalid"
DOCS_DIR = REPO_ROOT / "docs"


def _load_doc(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def _registry() -> Registry:
    """Register every schema (all versions) by its $id so cross-version
    absolute $refs (v1alpha2 -> v1alpha1) resolve."""
    registry = Registry()
    for schema_path in list(SCHEMA_DIR.glob("*.json")) + list(SCHEMA_DIR_V2.glob("*.json")):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        registry = registry.with_resource(
            schema["$id"], Resource.from_contents(schema)
        )
    return registry


def _schema_dir_for(case: dict) -> Path:
    return SCHEMA_DIRS[case.get("version", "v1alpha1")]


SCHEMA_FILES = sorted(SCHEMA_DIR.glob("*.json"))
SCHEMA_FILES_V2 = sorted(SCHEMA_DIR_V2.glob("*.json"))
ALL_SCHEMA_FILES = SCHEMA_FILES + SCHEMA_FILES_V2
CASES = _load_doc(EXAMPLE_DIR / "index.json")["cases"]
INVALID_CASES = _load_doc(INVALID_DIR / "index.json")["cases"]

# Keys that must never appear carrying a plaintext secret value in a fixture.
_FORBIDDEN_SECRET_KEYS = {"value", "secret", "plaintext", "ciphertext", "api_key", "password", "token"}
# Signature/credential reference fields legitimately use these names for
# non-secret references; allow them explicitly.
_ALLOWED_VALUE_CONTEXT = {"enrollment_token"}  # single-use, short-lived, not a standing secret


@pytest.mark.parametrize(
    "schema_path", ALL_SCHEMA_FILES, ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_schema_is_valid_2020_12(schema_path: Path):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert "$id" in schema, f"{schema_path.name} is missing $id"
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    "case", CASES, ids=lambda c: f"{c.get('version', 'v1alpha1')}/{c['example']}"
)
def test_example_validates_against_schema(case: dict):
    schema = json.loads((_schema_dir_for(case) / case["schema"]).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, registry=_registry())
    document = _load_doc(EXAMPLE_DIR / case["example"])
    errors = sorted(validator.iter_errors(document), key=lambda e: str(e.path))
    assert not errors, "\n".join(
        f"{list(e.path)}: {e.message}" for e in errors
    )


@pytest.mark.parametrize(
    "case", INVALID_CASES, ids=lambda c: c["example"]
)
def test_invalid_examples_are_rejected(case: dict):
    """Negative fixtures MUST fail validation — they guard the schema invariants."""
    schema = json.loads((_schema_dir_for(case) / case["schema"]).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, registry=_registry())
    document = _load_doc(INVALID_DIR / case["example"])
    assert list(validator.iter_errors(document)), (
        f"{case['example']} should be REJECTED: {case.get('reason', '')}"
    )


def test_every_schema_has_an_example():
    referenced = {c["schema"] for c in CASES}
    # common.defs is a shared $defs library; setup.task is exercised transitively
    # through setup.plan (its items $ref setup.task). Neither is instantiated alone.
    indirect = {"common.defs.schema.json", "setup.task.schema.json"}
    expected = {p.name for p in ALL_SCHEMA_FILES if p.name not in indirect}
    assert expected <= referenced, f"schemas without an example: {expected - referenced}"


@pytest.mark.parametrize(
    "example_path",
    sorted(list(EXAMPLE_DIR.glob("*.json")) + list(EXAMPLE_DIR.glob("*.yaml"))),
    ids=lambda p: p.name,
)
def test_no_plaintext_secret_values(example_path: Path):
    if example_path.name == "index.json":
        return
    document = _load_doc(example_path)

    def walk(node, key_path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                lowered = str(k).lower()
                if lowered in _FORBIDDEN_SECRET_KEYS and k not in _ALLOWED_VALUE_CONTEXT:
                    # Only signature.value (base64 signature, not a secret) is allowed.
                    assert "signature" in key_path or "hub_public_key" in key_path or "public_key" in key_path, (
                        f"{example_path.name}: suspicious secret-bearing key '{k}' at {key_path}"
                    )
                walk(v, f"{key_path}.{k}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{key_path}[{i}]")

    walk(document)


def _validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=_registry())


def _base_desired_state() -> dict:
    return json.loads(
        (EXAMPLE_DIR / "desired-state.example.json").read_text(encoding="utf-8")
    )


def test_age_is_rejected_as_signing_algorithm():
    """age is envelope encryption only; it must never validate as a signature."""
    common = json.loads((SCHEMA_DIR / "common.defs.schema.json").read_text(encoding="utf-8"))
    sig_schema = {"$schema": common["$schema"], **common["$defs"]["Signature"]}
    validator = Draft202012Validator(sig_schema)
    bad = {"algorithm": "age", "key_id": "k", "value": "x", "canonicalization": "jcs"}
    assert list(validator.iter_errors(bad)), "age must not be a valid Signature.algorithm"
    good = {"algorithm": "ed25519", "key_id": "k", "value": "x", "canonicalization": "jcs"}
    assert not list(validator.iter_errors(good))


def test_desired_state_requires_ed25519_and_rejects_sigstore_and_age():
    """The control plane pins ed25519; Sigstore/keyless and age are rejected."""
    validator = _validator("desired-state.schema.json")
    for bad_alg in ("sigstore-cosign", "age", "minisign"):
        doc = _base_desired_state()
        doc["signature"]["algorithm"] = bad_alg
        assert list(validator.iter_errors(doc)), (
            f"desired-state must reject signature algorithm {bad_alg!r}"
        )
    # The unmodified ed25519 example (with trust_domain) must still validate,
    # proving Sigstore/transparency-log availability is NOT required here.
    assert not list(validator.iter_errors(_base_desired_state()))


def test_desired_state_requires_trust_domain():
    validator = _validator("desired-state.schema.json")
    doc = _base_desired_state()
    doc["signature"].pop("trust_domain", None)
    assert list(validator.iter_errors(doc)), "desired-state signature must require trust_domain"


def test_pack_requires_spdx_license():
    validator = _validator("nexus.pack.schema.json")
    pack = yaml.safe_load(
        (EXAMPLE_DIR / "pack.real-estate-agency.yaml").read_text(encoding="utf-8")
    )
    assert not list(validator.iter_errors(pack))
    pack["metadata"].pop("license", None)
    assert list(validator.iter_errors(pack)), "pack must require an SPDX license"


def test_pack_offline_signature_only_minisign_or_ed25519():
    validator = _validator("nexus.pack.schema.json")
    pack = yaml.safe_load(
        (EXAMPLE_DIR / "pack.real-estate-agency.yaml").read_text(encoding="utf-8")
    )
    pack["metadata"]["offline_signature"]["algorithm"] = "sigstore-cosign"
    assert list(validator.iter_errors(pack)), (
        "offline_signature must reject sigstore-cosign (no offline infra dependency)"
    )


def test_secrets_manifest_forbids_ciphertext_and_requires_age_x25519():
    validator = _validator("secrets-bundle-manifest.schema.json")
    manifest = json.loads(
        (EXAMPLE_DIR / "secrets-bundle-manifest.example.json").read_text(encoding="utf-8")
    )
    assert not list(validator.iter_errors(manifest))
    # Any entry carrying ciphertext/plaintext must be rejected by construction.
    leaky = json.loads(json.dumps(manifest))
    leaky["entries"][0]["ciphertext"] = "AAAA"
    assert list(validator.iter_errors(leaky)), "manifest entries must forbid ciphertext"
    # age/X25519 recipient is mandatory; a non-age scheme must be rejected.
    non_age = json.loads(json.dumps(manifest))
    non_age["encryption"]["scheme"] = "jwe"
    assert list(validator.iter_errors(non_age)), "secrets bundle must pin age scheme"


def _validator_v2(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR_V2 / schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=_registry())


def _base_entitlement() -> dict:
    return json.loads(
        (EXAMPLE_DIR / "entitlement.team.example.json").read_text(encoding="utf-8")
    )


def test_entitlement_pins_ed25519_and_rejects_sigstore_and_age():
    """Entitlements verify offline with a pinned Hub key: only ed25519 signs."""
    validator = _validator_v2("entitlement.schema.json")
    assert not list(validator.iter_errors(_base_entitlement()))
    for bad_alg in ("sigstore-cosign", "age", "minisign", "ecdsa-p256"):
        doc = _base_entitlement()
        doc["signature"]["algorithm"] = bad_alg
        assert list(validator.iter_errors(doc)), (
            f"entitlement must reject signature algorithm {bad_alg!r}"
        )


def test_entitlement_requires_replay_and_expiry_fields():
    """Signed-envelope shape: nonce, revision and expiry are mandatory."""
    validator = _validator_v2("entitlement.schema.json")
    for field in ("nonce", "revision", "expires_at"):
        doc = _base_entitlement()
        doc["metadata"].pop(field, None)
        assert list(validator.iter_errors(doc)), f"entitlement must require metadata.{field}"
    # And the trust_domain the verifier resolves the key against.
    doc = _base_entitlement()
    doc["signature"].pop("trust_domain", None)
    assert list(validator.iter_errors(doc)), "entitlement signature must require trust_domain"


def test_subscription_never_holds_data_hostage():
    """Owner access and export are preserved in EVERY state; pinned by construction."""
    validator = _validator_v2("subscription-state.schema.json")
    good = json.loads(
        (EXAMPLE_DIR / "subscription-state.expired-downgrade.example.json").read_text(encoding="utf-8")
    )
    assert not list(validator.iter_errors(good))
    revoked = json.loads(json.dumps(good))
    revoked["spec"]["owner_access"] = "revoked"
    assert list(validator.iter_errors(revoked)), "owner_access must be preserved"
    no_export = json.loads(json.dumps(good))
    no_export["spec"]["export_available"] = False
    assert list(validator.iter_errors(no_export)), "export must always be available"


def test_subscription_expired_pauses_not_deletes():
    """Expired/suspended pause premium agents and tasks, never delete them."""
    validator = _validator_v2("subscription-state.schema.json")
    doc = json.loads(
        (EXAMPLE_DIR / "subscription-state.expired-downgrade.example.json").read_text(encoding="utf-8")
    )
    # 'paused' is the only non-running enum value; there is intentionally no
    # 'deleted'/'removed' state for premium_agents or scheduled_tasks.
    schema = json.loads((SCHEMA_DIR_V2 / "subscription-state.schema.json").read_text(encoding="utf-8"))
    effects = schema["properties"]["spec"]["properties"]["effects"]["properties"]
    assert set(effects["premium_agents"]["enum"]) == {"running", "paused"}
    assert set(effects["scheduled_tasks"]["enum"]) == {"running", "paused"}
    # An expired doc that keeps premium agents running is rejected.
    doc["spec"]["effects"]["premium_agents"] = "running"
    assert list(validator.iter_errors(doc))


def test_new_invitations_forced_blocked_only_in_degraded_states():
    """new_invitations is pinned to blocked ONLY in suspended/cancelled/expired.

    In active/past_due/grace it is policy, NOT pinned: an active instance may
    allow invitations while a lapsing one (e.g. grace) may still block seats.
    Both must validate. This documents the intentional non-pinning (L-c)."""
    validator = _validator_v2("subscription-state.schema.json")
    # active with invitations allowed (the shipped example) validates.
    active = _example("subscription-state.active.example.json")
    assert not list(validator.iter_errors(active))
    # active that chooses to block invitations ALSO validates: not pinned.
    active_blocked = json.loads(json.dumps(active))
    active_blocked["spec"]["effects"]["new_invitations"] = "blocked"
    assert not list(validator.iter_errors(active_blocked)), (
        "allowed states must NOT pin new_invitations (grace legitimately blocks)"
    )
    # grace blocking invitations (the shipped example) validates too.
    assert not list(validator.iter_errors(_example("subscription-state.grace.example.json")))
    # But a degraded state that tries to ALLOW invitations is rejected: pinned blocked.
    expired_allowing = _example("subscription-state.expired-downgrade.example.json")
    expired_allowing["spec"]["effects"]["new_invitations"] = "allowed"
    assert list(validator.iter_errors(expired_allowing)), (
        "expired/suspended/cancelled must force new_invitations blocked"
    )


def test_personal_base_pins_subscription_state_active_when_present():
    """personal_base has no Hub subscription to lapse (N1).

    subscription_state may be ABSENT (the shipped Personal example) or, if
    present, must be `active`; a degraded state under personal_base is rejected."""
    validator = _validator_v2("edition.declaration.schema.json")
    # Absent subscription_state (the shipped example) validates.
    assert not list(validator.iter_errors(_example("edition.personal.example.json")))
    # Explicit active is fine.
    ok = _example("edition.personal.example.json")
    ok["spec"]["subscription_state"] = "active"
    assert not list(validator.iter_errors(ok)), "personal_base may declare active explicitly"
    # A degraded state under personal_base is rejected.
    for degraded in ("past_due", "grace", "suspended", "cancelled", "expired"):
        bad = _example("edition.personal.example.json")
        bad["spec"]["subscription_state"] = degraded
        assert list(validator.iter_errors(bad)), (
            f"personal_base must reject subscription_state {degraded!r}"
        )


def test_public_packages_are_mirrorable_without_hub_account():
    validator = _validator_v2("package-access-policy.schema.json")
    doc = json.loads(
        (EXAMPLE_DIR / "package-access-policy.public.example.json").read_text(encoding="utf-8")
    )
    assert not list(validator.iter_errors(doc))
    doc["spec"]["mirrorable"] = False
    assert list(validator.iter_errors(doc)), "public packages must be mirrorable"
    doc = json.loads(
        (EXAMPLE_DIR / "package-access-policy.public.example.json").read_text(encoding="utf-8")
    )
    doc["spec"]["requires_hub_account"] = True
    assert list(validator.iter_errors(doc)), "public packages must not require a Hub account"


def test_premium_packages_require_entitlements():
    validator = _validator_v2("package-access-policy.schema.json")
    doc = json.loads(
        (EXAMPLE_DIR / "package-access-policy.premium.example.json").read_text(encoding="utf-8")
    )
    assert not list(validator.iter_errors(doc))
    doc["spec"].pop("required_entitlements", None)
    assert list(validator.iter_errors(doc)), "verified-premium must require entitlements"


def test_deployment_modality_is_orthogonal_but_forbids_managed_personal():
    """Edition and modality are independent axes; the only rejected pair is managed+personal."""
    validator = _validator_v2("deployment-modality.schema.json")
    for example in (
        "deployment-modality.personal-self-hosted.example.json",
        "deployment-modality.team-byoc.example.json",
        "deployment-modality.team-managed.example.json",
    ):
        doc = json.loads((EXAMPLE_DIR / example).read_text(encoding="utf-8"))
        assert not list(validator.iter_errors(doc)), f"{example} should validate"
    bad = json.loads(
        (INVALID_DIR / "deployment-modality.managed-personal.json").read_text(encoding="utf-8")
    )
    assert list(validator.iter_errors(bad)), "managed modality must reject personal edition"


def test_pack_premium_visibility_requires_entitlements():
    """The additive v1alpha1 pack extension ties restricted lanes to entitlements."""
    validator = _validator("nexus.pack.schema.json")
    pack = yaml.safe_load(
        (EXAMPLE_DIR / "pack.real-estate-agency.yaml").read_text(encoding="utf-8")
    )
    # Baseline (no visibility => public) still validates: backward compatible.
    assert not list(validator.iter_errors(pack))
    # Marking it premium without required_entitlements must fail.
    pack["metadata"]["visibility"] = "verified-premium"
    assert list(validator.iter_errors(pack)), "premium pack must declare required_entitlements"
    pack["spec"]["required_entitlements"] = ["premium_pack_access"]
    assert not list(validator.iter_errors(pack))


def _example(name: str) -> dict:
    return json.loads((EXAMPLE_DIR / name).read_text(encoding="utf-8"))


def test_edition_declaration_couples_source_edition_and_ref():
    """personal_base <=> edition personal + no entitlement_ref; verified/cached <=> paid edition + ref.

    Guards H1: the conditional must key off metadata.edition (top level), not the
    nonexistent spec.edition, so it actually fires."""
    validator = _validator_v2("edition.declaration.schema.json")
    assert not list(validator.iter_errors(_example("edition.personal.example.json")))
    assert not list(validator.iter_errors(_example("edition.team.example.json")))
    # personal_base claiming a paid edition must be rejected.
    bad = _example("edition.personal.example.json")
    bad["metadata"]["edition"] = "team"
    assert list(validator.iter_errors(bad)), "personal_base must force edition personal"
    # personal_base MUST NOT carry an entitlement_ref.
    bad = _example("edition.personal.example.json")
    bad["spec"]["entitlement_ref"] = {"revision": 1, "expires_at": "2027-01-01T00:00:00Z"}
    assert list(validator.iter_errors(bad)), "personal_base must not reference an entitlement"
    # verified_entitlement MUST carry an entitlement_ref.
    bad = _example("edition.team.example.json")
    bad["spec"].pop("entitlement_ref", None)
    assert list(validator.iter_errors(bad)), "verified_entitlement must carry entitlement_ref"
    # verified_entitlement MUST NOT declare edition personal.
    bad = _example("edition.team.example.json")
    bad["metadata"]["edition"] = "personal"
    assert list(validator.iter_errors(bad)), "verified_entitlement must be a paid edition"


def test_organization_policy_requires_exactly_one_owner():
    validator = _validator_v2("organization-policy.schema.json")
    good = _example("organization-policy.example.json")
    assert not list(validator.iter_errors(good))
    no_owner = json.loads(json.dumps(good))
    no_owner["spec"]["memberships"] = [
        {"user_ref": "usr_admin02", "role": "admin"},
    ]
    assert list(validator.iter_errors(no_owner)), "zero owners must be rejected"
    two_owners = json.loads(json.dumps(good))
    two_owners["spec"]["memberships"] = [
        {"user_ref": "usr_owner01", "role": "owner"},
        {"user_ref": "usr_owner02", "role": "owner"},
    ]
    assert list(validator.iter_errors(two_owners)), "two owners must be rejected"


def test_organization_id_is_lowercase_canonical():
    """A mixed-case org id cannot round-trip through a PackageScope, so it is rejected."""
    validator = _validator_v2("organization-policy.schema.json")
    bad = _example("organization-policy.example.json")
    bad["metadata"]["organization_id"] = "org_AbC123"
    assert list(validator.iter_errors(bad)), "OrganizationId must be lowercase-canonical"


def test_public_lane_requires_oss_fields():
    """Public/community MUST assert the OSS guarantee, not merely permit it (item 3)."""
    validator = _validator_v2("package-access-policy.schema.json")
    good = _example("package-access-policy.public.example.json")
    assert not list(validator.iter_errors(good))
    for field in ("mirrorable", "requires_hub_account", "distribution"):
        bad = _example("package-access-policy.public.example.json")
        bad["spec"].pop(field, None)
        assert list(validator.iter_errors(bad)), f"public lane must require spec.{field}"


def test_restricted_lane_pins_no_mirror_and_hub_account():
    """A grant-gated pack cannot advertise itself as freely mirrorable (item 4)."""
    validator = _validator_v2("package-access-policy.schema.json")
    good = _example("package-access-policy.premium.example.json")
    assert not list(validator.iter_errors(good))
    bad = _example("package-access-policy.premium.example.json")
    bad["spec"]["mirrorable"] = True
    assert list(validator.iter_errors(bad)), "restricted lane must pin mirrorable false"
    bad = _example("package-access-policy.premium.example.json")
    bad["spec"]["requires_hub_account"] = False
    assert list(validator.iter_errors(bad)), "restricted lane must pin requires_hub_account true"


def test_entitlement_organization_id_conditioned_on_edition():
    validator = _validator_v2("entitlement.schema.json")
    # personal must NOT carry organization_id.
    bad = _base_entitlement()
    bad["metadata"]["edition"] = "personal"
    bad["metadata"].pop("organization_id", None)
    bad["metadata"]["organization_id"] = "org_4b91e0"
    assert list(validator.iter_errors(bad)), "personal entitlement must not carry organization_id"
    # team MUST carry organization_id.
    bad = _base_entitlement()
    bad["metadata"].pop("organization_id", None)
    assert list(validator.iter_errors(bad)), "team entitlement must carry organization_id"


def test_download_grant_is_single_use_and_restricted_scope():
    validator = _validator_v2("package-download-grant.schema.json")
    good = _example("package-download-grant.example.json")
    assert not list(validator.iter_errors(good))
    bad = _example("package-download-grant.example.json")
    bad["spec"]["max_uses"] = 2
    assert list(validator.iter_errors(bad)), "grant is single-use (max_uses pinned to 1)"
    bad = _example("package-download-grant.example.json")
    bad["spec"]["scope"] = "public"
    assert list(validator.iter_errors(bad)), "grant scope must be a restricted lane, never public/community"


def test_managed_modality_requires_managed_by():
    validator = _validator_v2("deployment-modality.schema.json")
    bad = json.loads(
        (EXAMPLE_DIR / "deployment-modality.team-managed.example.json").read_text(encoding="utf-8")
    )
    bad["spec"].pop("managed_by", None)
    assert list(validator.iter_errors(bad)), "managed modality must require managed_by"


def test_pack_public_lane_forbids_entitlements():
    """OSS pack lanes must not gate on entitlements; legacy packs (no visibility) are untouched."""
    validator = _validator("nexus.pack.schema.json")
    pack = yaml.safe_load(
        (EXAMPLE_DIR / "pack.real-estate-agency.yaml").read_text(encoding="utf-8")
    )
    assert not list(validator.iter_errors(pack))  # no visibility => untouched
    pack["metadata"]["visibility"] = "public"
    pack["spec"]["required_entitlements"] = ["premium_pack_access"]
    assert list(validator.iter_errors(pack)), "public pack lane must forbid required_entitlements"


def test_docs_relative_links_resolve():
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    broken: list[str] = []
    for md in DOCS_DIR.rglob("*.md"):
        for match in link_re.finditer(md.read_text(encoding="utf-8")):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{md.relative_to(REPO_ROOT)} -> {target}")
    assert not broken, "Broken relative doc links:\n" + "\n".join(broken)


# One canonical document per role; superseded files are redirect stubs only.
CANONICAL_DOCS = {
    "vision": DOCS_DIR / "vision" / "nexus-os-vision.md",
    "architecture": DOCS_DIR / "architecture" / "nexus-os-architecture.md",
    "hub-dev-spec": DOCS_DIR / "specs" / "b-nexus-hub.md",
}
SUPERSEDED_STUBS = {
    DOCS_DIR / "vision" / "nexus-os-vision-managed-portal.md": "nexus-os-vision.md",
    DOCS_DIR / "vision" / "nexus-os-vision-personal-hub-subscription.md": "nexus-os-vision.md",
    DOCS_DIR / "architecture" / "managed-platform-architecture.md": "nexus-os-architecture.md",
}


def test_canonical_docs_exist():
    """Each canonical role resolves to exactly one existing document."""
    missing = [role for role, path in CANONICAL_DOCS.items() if not path.exists()]
    assert not missing, f"Missing canonical docs: {missing}"


def test_superseded_docs_are_redirect_stubs():
    """Superseded documents must be short stubs that flag themselves as
    superseded and link to the canonical replacement; they must not resurface
    as competing canonical specs."""
    problems: list[str] = []
    for path, canonical in SUPERSEDED_STUBS.items():
        if not path.exists():
            problems.append(f"{path.name}: expected superseded stub is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if "SUPERADO" not in text:
            problems.append(f"{path.name}: stub does not declare itself SUPERADO")
        if canonical not in text:
            problems.append(f"{path.name}: stub does not link to canonical {canonical}")
        # A stub is a redirect, not a full spec kept alive in parallel.
        if len(text.splitlines()) > 60:
            problems.append(f"{path.name}: stub too long to be a redirect ({len(text.splitlines())} lines)")
    assert not problems, "Superseded-doc stub problems:\n" + "\n".join(problems)


def test_single_canonical_hub_dev_spec():
    """The Hub development spec is unique: b-nexus-hub.md is canonical and the
    old portal architecture no longer competes as a Hub dev document."""
    hub_spec = CANONICAL_DOCS["hub-dev-spec"]
    assert hub_spec.exists()
    portal = DOCS_DIR / "architecture" / "managed-platform-architecture.md"
    assert "SUPERADO" in portal.read_text(encoding="utf-8"), (
        "managed-platform-architecture.md must be a superseded stub, not a "
        "competing Hub/architecture spec"
    )
