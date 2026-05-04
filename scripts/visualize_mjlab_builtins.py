"""Visualize built-in mjlab terrains in Viser.

This is a compact viewer for the terrain presets currently shipped with mjlab.
It shows one terrain family per column and sweeps difficulty from easy to hard
along the rows.

Examples:
  uv run python scripts/visualize_mjlab_builtins.py
"""

from __future__ import annotations

import dataclasses
import time
from typing import TypedDict

import mujoco
import viser

from mjlab.terrains.config import (
  ALL_TERRAINS_CFG,
  ROUGH_TERRAINS_CFG,
  STAIRS_TERRAINS_CFG,
)
from mjlab.terrains.terrain_generator import TerrainGenerator, TerrainGeneratorCfg
from mjlab.viewer.viser import merge_geoms


class _AppState(TypedDict):
  terrain_set: str
  rows: int
  seed: int
  difficulty_min: float
  difficulty_max: float


TERRAIN_SETS: dict[str, TerrainGeneratorCfg] = {
  "all": ALL_TERRAINS_CFG,
  "rough": ROUGH_TERRAINS_CFG,
  "stairs": STAIRS_TERRAINS_CFG,
}


def _build_cfg(state: _AppState) -> TerrainGeneratorCfg:
  base_cfg = TERRAIN_SETS[state["terrain_set"]]
  sub_terrains = {
    name: dataclasses.replace(cfg, proportion=1.0)
    for name, cfg in base_cfg.sub_terrains.items()
  }
  return dataclasses.replace(
    base_cfg,
    seed=state["seed"],
    curriculum=True,
    num_rows=state["rows"],
    num_cols=len(sub_terrains),
    difficulty_range=(state["difficulty_min"], state["difficulty_max"]),
    sub_terrains=sub_terrains,
  )


def main() -> None:
  server = viser.ViserServer(host="0.0.0.0", port=8080)
  state: _AppState = {
    "terrain_set": "all",
    "rows": 8,
    "seed": 42,
    "difficulty_min": 0.0,
    "difficulty_max": 1.0,
  }

  terrain_handle: viser.SceneNodeHandle | None = None
  origin_handles: list[viser.SceneNodeHandle] = []

  with server.gui.add_folder("Built-in Terrains"):
    terrain_set = server.gui.add_dropdown(
      "Terrain Set",
      options=tuple(TERRAIN_SETS.keys()),
      initial_value=state["terrain_set"],
    )
    rows = server.gui.add_slider("Rows", min=2, max=12, step=1, initial_value=state["rows"])
    seed = server.gui.add_number("Seed", initial_value=state["seed"])
    diff_min = server.gui.add_slider(
      "Difficulty Min",
      min=0.0,
      max=1.0,
      step=0.05,
      initial_value=state["difficulty_min"],
    )
    diff_max = server.gui.add_slider(
      "Difficulty Max",
      min=0.0,
      max=1.0,
      step=0.05,
      initial_value=state["difficulty_max"],
    )
    show_origins = server.gui.add_checkbox("Show Origins", initial_value=True)
    status = server.gui.add_markdown("**Status:** Ready")

  def regenerate() -> None:
    nonlocal terrain_handle, origin_handles
    status.content = "**Status:** Generating terrain..."

    cfg = _build_cfg(state)
    generator = TerrainGenerator(cfg)

    spec = mujoco.MjSpec()
    generator.compile(spec)
    model = spec.compile()
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    terrain_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "terrain")
    terrain_geom_ids = [
      i for i in range(model.ngeom) if model.geom_bodyid[i] == terrain_body_id
    ]
    if not terrain_geom_ids:
      status.content = "**Status:** No terrain geoms found"
      return

    terrain_mesh = merge_geoms(model, terrain_geom_ids)

    if terrain_handle is not None:
      terrain_handle.remove()
    for handle in origin_handles:
      handle.remove()
    origin_handles = []

    with server.atomic():
      terrain_handle = server.scene.add_mesh_trimesh("/terrain", terrain_mesh)
      if show_origins.value:
        for row in range(generator.terrain_origins.shape[0]):
          for col, name in enumerate(cfg.sub_terrains.keys()):
            origin = generator.terrain_origins[row, col]
            origin_handles.append(
              server.scene.add_frame(
                f"/origins/{row}_{col}",
                position=tuple(origin.tolist()),
                axes_length=0.35,
                axes_radius=0.01,
                origin_radius=0.02,
              )
            )

    names = ", ".join(cfg.sub_terrains.keys())
    status.content = (
      f"**Status:** {state['terrain_set']} | rows={cfg.num_rows} | "
      f"cols={cfg.num_cols} | terrains={names}"
    )

  @terrain_set.on_update
  def _(_) -> None:
    state["terrain_set"] = terrain_set.value
    regenerate()

  @rows.on_update
  def _(_) -> None:
    state["rows"] = int(rows.value)
    regenerate()

  @seed.on_update
  def _(_) -> None:
    state["seed"] = int(seed.value)
    regenerate()

  @diff_min.on_update
  def _(_) -> None:
    state["difficulty_min"] = float(diff_min.value)
    if state["difficulty_min"] > state["difficulty_max"]:
      state["difficulty_max"] = state["difficulty_min"]
      diff_max.value = state["difficulty_max"]
    regenerate()

  @diff_max.on_update
  def _(_) -> None:
    state["difficulty_max"] = float(diff_max.value)
    if state["difficulty_max"] < state["difficulty_min"]:
      state["difficulty_min"] = state["difficulty_max"]
      diff_min.value = state["difficulty_min"]
    regenerate()

  @show_origins.on_update
  def _(_) -> None:
    regenerate()

  regenerate()
  print("Viser terrain viewer running...")
  print("Open the Viser URL shown above in your browser.")
  while True:
    time.sleep(1.0)


if __name__ == "__main__":
  main()
