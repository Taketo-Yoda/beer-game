import { useState } from "react";
import { DebriefPage } from "./pages/DebriefPage";
import { GamePage } from "./pages/GamePage";
import { GameSetupPage } from "./pages/GameSetupPage";
import type { GameStateView } from "./types";

type View =
  | { name: "setup" }
  | { name: "playing"; state: GameStateView }
  | { name: "debrief"; gameId: string };

function App() {
  const [view, setView] = useState<View>({ name: "setup" });

  return (
    <main className="app-shell">
      {view.name === "setup" && (
        <GameSetupPage onStarted={(state) => setView({ name: "playing", state })} />
      )}
      {view.name === "playing" && (
        <GamePage
          state={view.state}
          onStateUpdated={(state) => setView({ name: "playing", state })}
          onFinished={() => setView({ name: "debrief", gameId: view.state.game_id })}
        />
      )}
      {view.name === "debrief" && <DebriefPage gameId={view.gameId} />}
    </main>
  );
}

export default App;
