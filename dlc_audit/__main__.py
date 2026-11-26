"""CLI: python -m dlc_audit {scan,validate,render} ..."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .common import load_json, save_json, utc_now
from .render import render_prompts, render_report
from .scan import run_scan
from .validate import validate_run


def cmd_scan(args: argparse.Namespace) -> int:
    run = run_scan(Path(args.target), args.profile)
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
    index = render_prompts(run, out_dir)
    report = render_report(run, out_dir, index, baseline)
    print(f"Informe: {report}")
    print(f"Prompts: {len(index)} en {out_dir / 'prompts'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dlc_audit", description="Auditor independiente de repositorios (solo lectura).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="Inventario y reglas deterministas.")
    p.add_argument("target", help="Ruta del repositorio objetivo (solo lectura).")
    p.add_argument("--out", help="Ruta de hallazgos.json (por defecto audits/<repo>/<run_id>/).")
    p.add_argument("--profile", default="default")
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
    p.add_argument("--force", action="store_true", help="Renderiza aunque falle la validación (borradores).")
    p.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
