"""amoc-utac command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="amoc-utac",
    help=(
        "AMOC-UTAC · GenesisAeon Package 18 — "
        "Atlantic Meridional Overturning Circulation collapse early warning."
    ),
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


@app.command()
def run(
    duration: int = typer.Option(120, "--duration", help="Simulation duration [years]"),
    scenario: str = typer.Option("SSP2-4.5", "--scenario", help="Climate scenario label"),
) -> None:
    """Run one AMOC-UTAC simulation cycle and display key results."""
    from amoc_utac.system import AmocUTAC

    console.print(
        Panel(
            f"[bold blue]AMOC-UTAC[/bold blue]  ·  Package 18  ·  "
            f"Scenario: [cyan]{scenario}[/cyan]",
            expand=False,
        )
    )

    system = AmocUTAC()
    result = system.run_cycle(duration_years=duration)
    crep = result["crep_state"]
    utac = result["utac_state"]

    # CREP table
    crep_table = Table(title="CREP Tensor State", show_header=True)
    crep_table.add_column("Component", style="cyan", no_wrap=True)
    crep_table.add_column("Value", style="green")
    crep_table.add_column("Description", style="dim")
    descriptions = {
        "C": "Critical slowing down (AR-1 autocorrelation)",
        "R": "Freshwater resonance at 34°S  (Fov signal)",
        "E": "Variance emergence (instability indicator)",
        "P": "Permutation entropy (raw, lower = more ordered)",
        "Gamma": "Composite CREP Γ  [target ≈ 0.251]",
    }
    for k, v in crep.items():
        crep_table.add_row(k, f"{v:.4f}", descriptions.get(k, ""))
    console.print(crep_table)

    # UTAC table
    utac_table = Table(title="UTAC State", show_header=True)
    utac_table.add_column("Variable", style="cyan", no_wrap=True)
    utac_table.add_column("Value", style="green")
    utac_table.add_row("H  (AMOC strength)", f"{utac['H']:.2f} Sv")
    utac_table.add_row("H* (tipping setpoint)", f"{utac['H_star']:.2f} Sv")
    utac_table.add_row("K  (reference strength)", f"{utac['K_eff']:.2f} Sv")
    utac_table.add_row("dH/dt", f"{utac['dH_dt']:.4f} Sv/yr")
    utac_table.add_row("Γ  (CREP)", f"{utac['Gamma']:.4f}")
    console.print(utac_table)

    # Ethics
    ethics = result["ethics"]
    level_colour = {"ALLOWED": "green", "WARNED": "yellow", "BLOCKED": "red"}
    colour = level_colour.get(ethics["level"], "white")
    console.print(
        f"\n[bold]Ethics-Gate:[/bold] "
        f"[{colour}]{ethics['level']}[/{colour}]  "
        f"(tension = {ethics['tension']:.3f})"
    )
    for caveat in ethics["caveats"]:
        console.print(f"  [yellow]⚠[/yellow]  {caveat}")

    console.print(
        f"\n[bold]Phase events detected:[/bold] {len(result['phase_events'])}"
    )


@app.command(name="tipping-estimate")
def tipping_estimate(
    method: str = typer.Option("utac", "--method", help="utac | statistical"),
    compare_ditlevsen: bool = typer.Option(
        True, "--compare-ditlevsen/--no-compare", help="Include Ditlevsen 2023 row"
    ),
) -> None:
    """Estimate the AMOC tipping year and compare with published literature."""
    from amoc_utac.system import AmocUTAC

    system = AmocUTAC()
    pred = system.predict_tipping_year()

    table = Table(title="AMOC Tipping-Year Estimates", show_lines=True)
    table.add_column("Source", style="cyan")
    table.add_column("Central Year", style="green")
    table.add_column("Range / Notes", style="yellow")

    table.add_row(
        "UTAC (Package 18)",
        f"{pred['utac_central_year']:.0f}",
        f"{pred['utac_5pct']:.0f} – {pred['utac_95pct']:.0f}  (5–95%)",
    )
    if compare_ditlevsen:
        lo, hi = pred["ditlevsen_2023_range"]
        table.add_row(
            "Ditlevsen & Ditlevsen (2023)",
            str(pred["ditlevsen_2023_central"]),
            f"{lo} – {hi}",
        )
    table.add_row(
        "Chavent et al. (2026)",
        f"≤ {pred['chavent_2026_50pct_by']}",
        "50% weakening threshold",
    )

    console.print(table)
    console.print(
        f"\nΓ_AMOC = {pred['gamma_amoc']:.4f}  "
        f"(H₀ = {pred['H0_sv']:.1f} Sv, "
        f"H* threshold = {pred['threshold_sv']:.1f} Sv)"
    )


@app.command(name="zenodo-export")
def zenodo_export(
    output: Path = typer.Option(
        Path("zenodo_record.json"), "--output", "-o", help="Output JSON file"
    ),
) -> None:
    """Export a Zenodo-compatible metadata record for this simulation run."""
    from amoc_utac.system import AmocUTAC

    system = AmocUTAC()
    system.run_cycle()

    try:
        record = system.to_zenodo_record()
    except RuntimeError as exc:
        err_console.print(f"[bold red]Export blocked:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    output.write_text(json.dumps(record, indent=2))
    crep = record["custom_fields"]["crep_state"]
    console.print(f"[green]Zenodo record written to:[/green] {output}")
    console.print(f"  Γ_AMOC = {crep['Gamma']:.4f}  (target: 0.251)")
    console.print(f"  Ethics level: {record['custom_fields']['ethics']['level']}")


if __name__ == "__main__":
    app()
