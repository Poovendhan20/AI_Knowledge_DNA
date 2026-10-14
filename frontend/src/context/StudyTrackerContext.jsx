/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import API from "../services/api";

const StudyTrackerContext = createContext(null);

const STORAGE_KEY_PREFIX = "ai_knowledge_dna_study_tracker_";
const IDLE_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes of inactivity
const TICK_INTERVAL_MS = 1000; // 1 second tick

// Active learning workspace routes
const isLearningRoute = (pathname) => {
  if (!pathname) return false;
  return (
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/document/") ||
    pathname.startsWith("/quiz/") ||
    pathname.startsWith("/voice-assistant")
  );
};

export function StudyTrackerProvider({ children }) {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  const [activeTopic, setActiveTopic] = useState("General");

  // Derive studying state pure from auth and current route
  const isStudying = Boolean(isAuthenticated && isLearningRoute(location.pathname));

  const accumulatedSecondsRef = useRef(0);
  const lastTickRef = useRef(0);
  const lastActivityRef = useRef(0);
  const isFlushingRef = useRef(false);
  const activeTopicRef = useRef("General");
  const timerIdRef = useRef(null);

  // Sync ref with state
  useEffect(() => {
    activeTopicRef.current = activeTopic || "General";
  }, [activeTopic]);

  const storageKey = user?.id ? `${STORAGE_KEY_PREFIX}${user.id}` : null;

  // Restore accumulated seconds from sessionStorage on login/route change
  useEffect(() => {
    if (!storageKey) return;
    try {
      const stored = sessionStorage.getItem(storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (typeof parsed?.accumulatedSeconds === "number" && parsed.accumulatedSeconds >= 0) {
          accumulatedSecondsRef.current = Math.min(parsed.accumulatedSeconds, 3600);
        }
      }
    } catch {
      // Storage unavailable or invalid JSON
    }
  }, [storageKey]);

  // Save accumulated seconds to sessionStorage
  const persistSeconds = useCallback(() => {
    if (!storageKey) return;
    try {
      sessionStorage.setItem(
        storageKey,
        JSON.stringify({
          accumulatedSeconds: accumulatedSecondsRef.current,
          lastSaved: Date.now(),
        })
      );
    } catch {
      // Ignore storage errors
    }
  }, [storageKey]);

  // Flush completed minutes to the backend /api/learning/session
  const flushMinutes = useCallback(async () => {
    if (isFlushingRef.current) return;
    const wholeMinutes = Math.floor(accumulatedSecondsRef.current / 60);
    if (wholeMinutes < 1) return;

    isFlushingRef.current = true;
    const topicToRecord = activeTopicRef.current || "General";
    const secondsDeducted = wholeMinutes * 60;
    accumulatedSecondsRef.current -= secondsDeducted;
    persistSeconds();

    try {
      const response = await API.post("/learning/session", {
        topic: topicToRecord,
        study_minutes: wholeMinutes,
      });

      if (response?.data?.success) {
        // Dispatch event for UI components (Dashboard, etc.) to refresh stats
        window.dispatchEvent(
          new CustomEvent("ai-knowledge-dna:study-session-updated", {
            detail: {
              topic: topicToRecord,
              study_minutes: wholeMinutes,
              alreadyRecorded: true,
              data: response.data,
            },
          })
        );
      } else {
        // Re-add deducted seconds if recording was rejected
        accumulatedSecondsRef.current += secondsDeducted;
        persistSeconds();
      }
    } catch (err) {
      console.error("Study session recording error:", err);
      // Restore on failure
      accumulatedSecondsRef.current += secondsDeducted;
      persistSeconds();
    } finally {
      isFlushingRef.current = false;
    }
  }, [persistSeconds]);

  // Activity listeners to detect user presence
  useEffect(() => {
    const handleActivity = () => {
      lastActivityRef.current = Date.now();
    };

    const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
    events.forEach((ev) => window.addEventListener(ev, handleActivity, { passive: true }));

    return () => {
      events.forEach((ev) => window.removeEventListener(ev, handleActivity));
    };
  }, []);

  // Main active tracking loop
  useEffect(() => {
    if (!isStudying) {
      if (timerIdRef.current) {
        clearInterval(timerIdRef.current);
        timerIdRef.current = null;
      }
      return;
    }

    lastTickRef.current = Date.now();
    lastActivityRef.current = Date.now();

    const tick = () => {
      // 1. Check tab visibility
      if (typeof document !== "undefined" && document.visibilityState === "hidden") {
        lastTickRef.current = Date.now();
        return;
      }

      // 2. Check user inactivity
      const now = Date.now();
      const isIdle = now - lastActivityRef.current > IDLE_TIMEOUT_MS;
      if (isIdle) {
        lastTickRef.current = now;
        return;
      }

      // 3. Compute monotonic delta
      const deltaMs = now - lastTickRef.current;
      lastTickRef.current = now;

      // Bound delta to prevent large jumps if computer slept
      const deltaSeconds = Math.min(Math.floor(deltaMs / 1000), 10);
      if (deltaSeconds > 0) {
        accumulatedSecondsRef.current += deltaSeconds;
        persistSeconds();

        // If at least 1 full minute has accumulated, flush to backend
        if (accumulatedSecondsRef.current >= 60) {
          flushMinutes();
        }
      }
    };

    timerIdRef.current = setInterval(tick, TICK_INTERVAL_MS);

    // Visibility change handler
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        flushMinutes();
      } else {
        lastTickRef.current = Date.now();
        lastActivityRef.current = Date.now();
      }
    };

    // Before unload handler to save pending time
    const handleBeforeUnload = () => {
      persistSeconds();
      if (accumulatedSecondsRef.current >= 60) {
        flushMinutes();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      if (timerIdRef.current) {
        clearInterval(timerIdRef.current);
        timerIdRef.current = null;
      }
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("beforeunload", handleBeforeUnload);
      persistSeconds();
      flushMinutes();
    };
  }, [isStudying, flushMinutes, persistSeconds]);

  const setStudyTopic = useCallback((topic) => {
    setActiveTopic(topic || "General");
  }, []);

  const getAccumulatedSeconds = useCallback(() => {
    return accumulatedSecondsRef.current;
  }, []);

  const value = useMemo(
    () => ({
      activeTopic,
      setStudyTopic,
      isStudying,
      getAccumulatedSeconds,
      flushMinutes,
    }),
    [activeTopic, setStudyTopic, isStudying, getAccumulatedSeconds, flushMinutes]
  );

  return (
    <StudyTrackerContext.Provider value={value}>
      {children}
    </StudyTrackerContext.Provider>
  );
}

export function useStudyTracker() {
  const context = useContext(StudyTrackerContext);
  if (!context) {
    return {
      activeTopic: "General",
      setStudyTopic: () => {},
      isStudying: false,
      getAccumulatedSeconds: () => 0,
      flushMinutes: () => {},
    };
  }
  return context;
}
