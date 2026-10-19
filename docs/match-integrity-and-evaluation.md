# A shot-quality summary requires a coherent match artifact

Method update: October 18, 2026.

The offline loader now rejects nonfinite or out-of-range xG, shots attributed to a team outside the match, invalid scoreline counts and a shot-goal total that disagrees with the declared score. This prevents malformed data from silently disappearing from team rollups or producing a false headline. Incomplete event feeds and own-goal conventions must be normalized before loading this complete-match artifact format.

These checks establish internal consistency. They do not establish xG calibration or identify a player's finishing skill from one match. A single-game gap between goals and xG is a descriptive result affected by outcome variation.

For the next proposed evaluation, split by match and time before tuning a model or threshold. Keep every event from one match in the same split. Evaluate calibration by shot-quality slice and report the number of matches and shots, including missing-feed exclusions. Use later matchdays for a final held-out check. No betting data, odds or trading action is introduced by this refresh.
