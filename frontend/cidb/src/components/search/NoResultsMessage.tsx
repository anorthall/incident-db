import { useId, useMemo } from "react";

const NO_RESULTS_PHRASES = [
  "Keep on diggin'",
  "Nothin' down that hole!",
  "Cave's empty, friend",
  "No bats in this belfry",
  "Spelunked and found zilch",
  "The abyss stares back... blankly",
  "Even the stalactites shrugged",
  "This passage leads nowhere",
  "Nada in the dark",
  "The cave gods say no",
  "Squeezed through and found squat",
  "Not a single drip",
  "The void is strong with this one",
  "Helmet lamp's on, results are off",
  "Rock solid nothing",
  "Explored every crevice...",
  "This chamber's got cobwebs only",
  "Rappelled down to zero results",
  "The echoes came back empty",
  "Survey says: nothin'",
  "Crawled through mud for this?",
  "Even the cave crickets left",
  "Bottomless pit of no results",
  "The grotto giveth not",
];

export function NoResultsMessage() {
  const id = useId();
  const phrase = useMemo(() => {
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
      hash = (hash * 31 + id.charCodeAt(i)) | 0;
    }
    const index = Math.abs(hash) % NO_RESULTS_PHRASES.length;
    return NO_RESULTS_PHRASES[index];
  }, [id]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="flex flex-col gap-6 text-center">
        <p className="animate-no-results text-6xl font-bold leading-normal bg-linear-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 bg-size-[200%_100%] animate-gradient-x bg-clip-text text-transparent">
          {phrase}
        </p>
      </div>
    </div>
  );
}
