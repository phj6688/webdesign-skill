# A 3D element from an image

Source: img2threejs (Apache-2.0), distilled to what a web page needs. Restated; see
`NOTICE.md`.

This covers building an interactive three.js object for a web page, from a reference
image, in code only: no downloaded meshes, no baked textures. It distills the doctrine of
the `img2threejs` project.

**Know which job you have.** A hero object, a product turntable or a decorative scene is
a page job, and this file covers it. A detail-accurate reconstruction of a specific
object, or a rigged, animation-ready character, is a pipeline job. The upstream project
runs that pipeline with dozens of validators and a render-and-review loop, and the
project's own docs estimate 80,000 to 350,000 tokens and five to eight review cycles per
object. Install it and use it directly for that:

```
git clone https://github.com/img2threejs/img2threejs ~/.claude/skills/img2threejs
```

Do not reproduce its pipeline by hand from this file.

## Map the subject onto primitives

Decompose the reference into parts, then pick the primitive that matches each part's
form. The choice matters more than the triangle count.

| Primitive | For |
|---|---|
| box | flat machinery, furniture, panels, blockout masses |
| sphere or ellipsoid | fruit, knobs, organic joints, rounded stones, heads |
| cylinder, cone, capsule | trunks, pipes, limbs, handles, bottles |
| torus | rings, tyres, loops, trim, coiled cable |
| extruded shape | logos, flat ornamental plates, blades, keys, leaves |
| lathe | vases, bottles, bowls, lamps, wheels, anything turned |
| tube along a curve | cables, roots, branches, straps, hoses of constant radius |
| tapered sweep | horns, tails, claws, blade tips, hair locks: a curved spine ending in a point |
| instanced mesh | screws, rivets, leaves, scales, pebbles, any repeated small part |
| plane cards | thin leaves, feathers, labels, cloth strips |

A tube keeps a constant radius, so it can never come to a point. Use a tapered sweep for
anything that narrows to a tip, and frame it with parallel transport rather than the
default Frenet frames, which flip 180 degrees at an inflection and twist the geometry.

A plane card needs an alpha texture to read as hair or fur. Code-only work cannot
produce one, so do not use plane cards for hair.

## Flat is the common failure

A model can match the reference silhouette almost perfectly and still be a flat slab.
One real reconstruction scored 0.986 on silhouette overlap and was still rejected as
"just a projection", because every part was an extrusion with depth added on.

Check it by counting planes. For each mesh, round its vertex Z values to about 0.001 and
count the distinct values. An extrusion with a bevel lands on 6 to 10 planes regardless
of triangle count. A genuinely revolved or lofted part lands on 11 or more. Triangle
count is not evidence of form. Plane count is.

## Left and right

Fix one frame and keep it: Y up, forward along positive Z, right-handed.

A mirrored pair is a **reflection**, `(x, y, z)` to `(-x, y, z)`. It is never a
rotation. A rotation preserves handedness and silently produces two right hands. A
reflection also reverses triangle winding, so flip the winding back, or flat shading
lights the mirrored part as if the light came from behind.

## Look at it from every side

A single front view is not evidence. Holes through a surface, a part at the wrong height
and parts floating free all survive front-only review. Capture at least four angles:
0, 90, 180 and 270 degrees.

For a repeatable capture, the review camera must be deterministic:

- Disable the orbit controls during capture (`controls.enabled = false`). Their
  per-frame update overrides a scripted camera position and makes shots
  unreproducible.
- Pin the viewport to fixed dimensions at a device pixel ratio of 1.
- Frame the object so it fills about 98% of the reference's width, matching the
  reference photo, so a framing difference does not read as a shape difference.

`scripts/shoot.sh` captures the page. For the angles, render each view to its own URL
state, such as `?view=90`, and shoot each one.

## Light it three ways

A material that only convinces under one light has not passed. Look at every material
under three setups before accepting it:

- **Neutral.** A broad, soft key and fill, for honest base colour.
- **Grazing.** A low, hard key that exposes weak normals, flat roughness and tiling.
- **Reference match.** The reference photo's camera and light, as closely as you can
  infer them.

A complete lighting setup declares: the key light's direction, colour temperature,
intensity and shadow softness; a fill, or a stated reason for none; a rim or environment
reflection; the ambient or hemisphere colour; exposure and tone mapping; the background;
and how contact shadows behave.

Renderer settings that go with it:

```js
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0; // calibrate once, never per material

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
pmrem.dispose();
```

Colour textures take `THREE.SRGBColorSpace`. Data maps (roughness, normal, metalness)
stay `THREE.NoColorSpace`. Getting this wrong is the usual reason a material looks
washed out.

## Versions and imports

Pin the version in `package.json`. The upstream pipeline's generated code and material
rules are measured against `three@0.169.0`, so pin exactly that when you run it. For a
standalone hero, pin the current release.

Import through a bundler, with bare specifiers:

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
```

`three/examples/jsm/...` is the older spelling of the same path, and it still resolves.

Ship the object as a factory function that returns a `THREE.Group`, so the page owns the
scene, the camera and the render loop:

```js
export function createLampModel(options = {}) {
  const root = new THREE.Group();
  // parts, materials, sockets
  return root;
}
```

## On the page

A 3D element is the heaviest thing on most pages, so it gets its own rules.

- **Load it lazily.** Three.js is large. Import it dynamically when the canvas nears the
  viewport, never in the main bundle.
- **Reserve its space.** Give the canvas container a fixed aspect ratio before the
  script loads, so it causes no layout shift.
- **Show a poster first.** Render a static image of the object in the container, and
  replace it once the scene is ready. It is also the fallback when WebGL is unavailable.
- **Respect reduced motion.** Under `prefers-reduced-motion: reduce`, stop the
  auto-rotation and any idle animation. User-driven orbiting can stay.
- **Cap the pixel ratio** at 2. A phone at 3x triples the fill cost for no visible gain.
- **Pause when hidden.** Stop the render loop when the canvas leaves the viewport or the
  tab is hidden.
- **Clean up.** Dispose geometries, materials, textures and the renderer on unmount.
- **Isolate it.** The canvas lives in its own leaf client component. Do not put a
  three.js scene and a motion library in the same component tree; they fight over the
  same frames.
- **Give it an accessible name.** The canvas is an image to a screen reader, so give it
  a role and a label that says what the object is.

It is one memorable moment. If the page already has one, it does not need a second.
