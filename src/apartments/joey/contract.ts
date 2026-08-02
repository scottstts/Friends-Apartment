/** Observable visual contract derived only from build_scripts/Joeys_apt. */
export const JOEY_VISUAL_CONTRACT = {
  subject: "Chandler and Joey's apartment 19",
  identity: [
    'stepped north wall with the kitchen pulled south into a shallow alcove',
    'cool moonlit night ambience from the north-facing light well against warm practical fixtures',
    'continuous 12-inch five-finger mosaic parquet through living room and bedrooms',
    'yellow couch, two inward-splayed black recliners, entertainment wall and foosball table',
    'cream-and-putty L-shaped kitchen with vintage range, retro fridge and peninsula stools',
    'five-horizontal-panel open interior doors and greige applied wall mouldings',
  ],
  materialSeparation: [
    'honey oak parquet remains distinct from painted trim and cabinet timber',
    'black leather recliners retain broad coated highlights without reading as plastic',
    'brass, chrome, enamel, clear glass and glazed ceramic remain distinct before bloom',
    'poster art uses the supplied image assets without substitution',
  ],
  invariants: [
    'the JX/NY2 reflex corner owns no overlapping wall volume',
    'the peninsula turns on the jog wall and the counter reaches the east wall without a gap',
    'both recliners face west toward the entertainment unit and splay toward each other',
    'all door and window openings remain passable and their casings do not intersect the leaves',
    'the front-door threshold is floored and the player remains enclosed by authored colliders',
    'apartment 19 owns its scene, material cache, layout constants and interaction anchors',
  ],
  allowedDivergences: [
    'User-approved: replace the Blender build daytime physical sky with apartment 20\'s night sky, moon and distant-city ambience while retaining apartment 19 exterior geometry and fixture-authored practical lighting.',
  ] as string[],
  frameBudgetMs: 16.7,
} as const
