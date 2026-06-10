"""Merge ground plane + box_tall into a single OBJ file."""

from pathlib import Path

DATA_DIR = Path("src/holosoma/holosoma/data/motions/g1_29dof/whole_body_tracking")

ground = (DATA_DIR / "terrain_climb_14.obj").read_text()
box = (DATA_DIR / "terrain_climb_14_box_tall.obj").read_text()

# Parse vertices and faces from an OBJ string
def parse_obj(text: str):
    verts, faces = [], []
    for line in text.strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            verts.append(parts[1:])
        elif parts[0] == "f":
            faces.append(parts[1:])
    return verts, faces

g_verts, g_faces = parse_obj(ground)
b_verts, b_faces = parse_obj(box)

# Write merged OBJ
out = DATA_DIR / "terrain_climb_14_ground_box_tall.obj"
with open(out, "w") as f:
    f.write("# Merged: ground plane + tall box\n")
    # Ground vertices
    for v in g_verts:
        f.write(f"v {v[0]} {v[1]} {v[2]}\n")
    # Box vertices
    for v in b_verts:
        f.write(f"v {v[0]} {v[1]} {v[2]}\n")
    # Ground faces (1-indexed, unchanged)
    for face in g_faces:
        f.write(f"f {' '.join(face)}\n")
    # Box faces (offset vertex indices by len(g_verts))
    offset = len(g_verts)
    for face in b_faces:
        shifted = [str(int(idx) + offset) for idx in face]
        f.write(f"f {' '.join(shifted)}\n")

print(f"Wrote {out}  (ground verts: {len(g_verts)}, box verts: {len(b_verts)})")
