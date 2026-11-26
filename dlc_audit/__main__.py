"""CLI: python -m dlc_audit {scan,validate,render} ..."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .closure import check_closure, cross_check
from .common import load_json, save_json, utc_now
from .gitops import GitError, fetch, publish
from .render import render_integrator_prompt, render_prompts, render_report
from .scan import run_scan
from .validate import validate_run


def cmd_scan(args: argparse.Namespace) -> int:
    baseline = load_json(Path(args.baseline)) if args.baseline else None
    run = run_scan(Path(args.target), args.profile, ref=args.ref, baseline=baseline)
    out = Path(args.out) if args.out else Path("audits") / run["target"]["name"] / run["run_id"] / "hallazgos.json"
    save_json(out, run)
    pending = [r["id"] for r in run["rules"] if r["status"] == "pending"]
    print(f"Run: {run['run_id']}")
    print(f"Archivo: {out}")
    print(f"Archivos: {run['coverage']['files_total']} | hallazgos deterministas: {len(run['findings'])}")
    print(f"Reglas pendientes de juicio ({len(pending)}): {', '.join(pending) or 'ninguna'}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.run)
    run = load_json(path)
    if args.final and not run.get("finished_at"):
        run["finished_at"] = utc_now()
    errors, warnings = validate_run(run, Path(args.target) if args.target else None,
                                    final=args.final, assign_ids=args.assign_ids)
    for w in warnings:
        print(f"AVISO: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if args.assign_ids or args.final:
        save_json(path, run)
    print(f"Resultado: {len(errors)} error(es), {len(warnings)} aviso(s).")
    return 1 if errors else 0


def cmd_render(args: argparse.Namespace) -> int:
    run = load_json(Path(args.run))
    errors, _ = validate_run(run, Path(args.target) if args.target else None, final=True)
    if errors and not args.force:
        for e in errors:
            print(f"ERROR: {e}")
        print("No se renderiza un run que no pasa 'validate --final' (use --force solo para borradores).")
        return 1
    out_dir = Path(args.out_dir) if args.out_dir else Path(args.run).parent
    baseline = load_json(Path(args.baseline)) if args.baseline else None
    closure = load_json(Path(args.closure)) if args.closure else None
    index = render_prompts(run, out_dir)
    integrator = render_integrator_prompt(run, out_dir)
    report = render_report(run, out_dir, index, baseline, closure=closure, has_integrator_prompt=integrator is not None)
    print(f"Informe: {report}")
    print(f"Prompts: {len(index)} en {out_dir / 'prompts'}")
    print(f"Prompt del integrador: {integrator or 'no aplica (sin hallazgos)'}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    try:
        info = fetch(args.source, Path(args.dest), args.ref)
    except GitError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Ruta: {info['path']}\nRama: {info['ref']}\nRevisión: {info['revision']}\nURL: {info['url']}")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    try:
        res = publish(Path(args.run), push=args.push, remote_url=args.remote_url)
    except GitError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Rama: {res['branch']} (base {res['base_revision'][:12]})")
    print(f"Archivos ({len(res['files'])}): " + ", ".join(res["files"][:5]) + (" ..." if len(res["files"]) > 5 else ""))
    print("Publicada." if res["pushed"] else "Simulación: no se empujó nada (use --push).")
    return 0


def cmd_closure(args: argparse.Namespace) -> int:
    baseline = load_json(Path(args.baseline))
    cierre = load_json(Path(args.cierre))
    check = check_closure(baseline, cierre, Path(args.repo))
    if args.new_run:
        cross_check(check, cierre, load_json(Path(args.new_run)))
    out = Path(args.out) if args.out else Path(args.cierre).with_name("closure-check.json")
    save_json(out, check)
    for e in check["errors"]:
        print(f"ERROR: {e}")
    for w in check["warnings"]:
        print(f"AVISO: {w}")
    if check.get("contradicted"):
        print("CONTRADICHAS: " + ", ".join(check["contradicted"]))
    print(f"Declarado: {check['claims']} | archivos cambiados: {len(check['changed_files'])} | salida: {out}")
    return 1 if check["errors"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dlc_audit", description="Auditor independiente de repositorios (solo lectura).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="Inventario y reglas deterministas.")
    p.add_argument("target", help="Ruta del repositorio objetivo (solo lectura).")
    p.add_argument("--out", help="Ruta de hallazgos.json (por defecto audits/<repo>/<run_id>/).")
    p.add_argument("--profile", default="default")
    p.add_argument("--ref", help="Nombre de la rama auditada (por defecto, la rama actual del clon).")
    p.add_argument("--baseline", help="hallazgos.json de la ronda anterior (fija ronda y baseline).")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("validate", help="Valida estructura, catálogo y evidencia.")
    p.add_argument("run")
    p.add_argument("--target", help="Sobrescribe la ruta del objetivo.")
    p.add_argument("--assign-ids", action="store_true", help="Calcula ids faltantes y guarda.")
    p.add_argument("--final", action="store_true", help="Exige run completo (sin reglas pendientes).")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="Genera informe.md y prompts/.")
    p.add_argument("run")
    p.add_argument("--out-dir", help="Por defecto, la carpeta del run.")
    p.add_argument("--target")
    p.add_argument("--baseline", help="hallazgos.json de una auditoría anterior.")
    p.add_argument("--closure", help="closure-check.json generado por el comando closure.")
    p.add_argument("--force", action="store_true", help="Renderiza aunque falle la validación (borradores).")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("fetch", help="Clona por enlace y deja el árbol en la rama o commit indicado.")
    p.add_argument("source", help="URL del repositorio (https/ssh) o ruta local.")
    p.add_argument("--ref", help="Rama, etiqueta o commit (por defecto, la rama por defecto del remoto).")
    p.add_argument("--dest", default="work", help="Carpeta de trabajo (ignorada por git).")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("publish", help="Publica la rama audit/<run_id> en el repositorio auditado.")
    p.add_argument("run")
    p.add_argument("--push", action="store_true", help="Empuja la rama. Sin esto solo simula.")
    p.add_argument("--remote-url", help="Sobrescribe la URL del remoto (por defecto, origin del clon).")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("closure", help="Verifica el cierre del integrador contra el repositorio.")
    p.add_argument("--baseline", required=True, help="hallazgos.json de la ronda auditada.")
    p.add_argument("--cierre", required=True, help="cierre.json entregado por el integrador.")
    p.add_argument("--repo", required=True, help="Clon del repositorio (con la rama del integrador ya traída).")
    p.add_argument("--new-run", help="hallazgos.json de la re-auditoría, para detectar correcciones contradichas.")
    p.add_argument("--out")
    p.set_defaults(func=cmd_closure)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: no se encontró {exc.filename or exc}.")
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON inválido ({exc}).")
    except GitError as exc:
        print(f"ERROR: {exc}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
