import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for detecting user inactivity, providing a grace warning period,
 * and synchronizing idle state across multiple browser tabs via BroadcastChannel.
 *
 * @param {Object} options
 * @param {Function} options.onIdle - Callback invoked when the inactivity countdown expires.
 * @param {number} [options.idleTimeoutMs=900000] - Total inactivity threshold (default: 15 minutes).
 * @param {number} [options.promptBeforeMs=60000] - Warning prompt duration before auto-logout (default: 60s).
 * @param {boolean} [options.enabled=true] - Whether the timer is actively listening.
 */
export function useIdleTimer({
  onIdle,
  idleTimeoutMs = 15 * 60 * 1000, // 15 minutes
  promptBeforeMs = 60 * 1000,      // 60 seconds
  enabled = true,
}) {
  const [isWarningOpen, setIsWarningOpen] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(Math.round(promptBeforeMs / 1000));

  const lastActivityRef = useRef(Date.now());
  const warningTimerRef = useRef(null);
  const countdownIntervalRef = useRef(null);
  const broadcastChannelRef = useRef(null);
  const lastBroadcastRef = useRef(0);

  // Clear all pending timeouts and intervals
  const clearTimers = useCallback(() => {
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
  }, []);

  // Graceful logout execution
  const triggerLogout = useCallback((reason = 'inactivity') => {
    clearTimers();
    setIsWarningOpen(false);

    // Notify other open tabs
    try {
      broadcastChannelRef.current?.postMessage({
        type: 'LOGOUT',
        reason,
        timestamp: Date.now(),
      });
    } catch {
      // BroadcastChannel fallback
    }

    if (onIdle) {
      onIdle(reason);
    }
  }, [clearTimers, onIdle]);

  // Start the warning countdown interval (e.g., 60 -> 0)
  const startCountdown = useCallback(() => {
    setIsWarningOpen(true);
    const totalSeconds = Math.round(promptBeforeMs / 1000);
    setRemainingSeconds(totalSeconds);

    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
    }

    const startTime = Date.now();
    countdownIntervalRef.current = setInterval(() => {
      const elapsedMs = Date.now() - startTime;
      const left = Math.max(0, totalSeconds - Math.floor(elapsedMs / 1000));
      setRemainingSeconds(left);

      if (left <= 0) {
        clearInterval(countdownIntervalRef.current);
        countdownIntervalRef.current = null;
        triggerLogout('inactivity');
      }
    }, 1000);
  }, [promptBeforeMs, triggerLogout]);

  // Reset the timer when user interaction occurs
  const resetIdleTimer = useCallback((broadcast = true) => {
    clearTimers();
    setIsWarningOpen(false);
    lastActivityRef.current = Date.now();
    setRemainingSeconds(Math.round(promptBeforeMs / 1000));

    if (!enabled) return;

    // Broadcast activity to other tabs (throttled to at most once every 3 seconds)
    if (broadcast) {
      const now = Date.now();
      if (now - lastBroadcastRef.current > 3000) {
        lastBroadcastRef.current = now;
        try {
          broadcastChannelRef.current?.postMessage({
            type: 'ACTIVITY',
            timestamp: now,
          });
        } catch {
          // Ignore BroadcastChannel errors
        }
      }
    }

    // Schedule the warning prompt
    const delayBeforeWarning = Math.max(0, idleTimeoutMs - promptBeforeMs);
    warningTimerRef.current = setTimeout(() => {
      startCountdown();
    }, delayBeforeWarning);
  }, [clearTimers, enabled, idleTimeoutMs, promptBeforeMs, startCountdown]);

  // Set up BroadcastChannel for cross-tab communication
  useEffect(() => {
    if (typeof window === 'undefined' || !('BroadcastChannel' in window)) {
      return;
    }

    try {
      const channel = new BroadcastChannel('glg_auth_sync');
      broadcastChannelRef.current = channel;

      channel.onmessage = (event) => {
        const { type, reason } = event.data || {};
        if (type === 'ACTIVITY') {
          // Another tab was active; reset our local timer without rebroadcasting
          resetIdleTimer(false);
        } else if (type === 'LOGOUT') {
          // Another tab logged out; log out locally
          clearTimers();
          setIsWarningOpen(false);
          if (onIdle) {
            onIdle(reason || 'remote_logout');
          }
        }
      };

      return () => {
        channel.close();
      };
    } catch (err) {
      console.warn('BroadcastChannel initialization failed:', err);
    }
  }, [clearTimers, onIdle, resetIdleTimer]);

  // Attach window activity listeners
  useEffect(() => {
    if (!enabled) {
      clearTimers();
      setIsWarningOpen(false);
      return;
    }

    resetIdleTimer(false);

    // Throttled event handler for DOM activity
    let lastHandled = 0;
    const handleUserActivity = () => {
      const now = Date.now();
      // Throttle event handling to once every 1.5 seconds
      if (now - lastHandled > 1500) {
        lastHandled = now;
        resetIdleTimer(true);
      }
    };

    const trackedEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'wheel'];
    trackedEvents.forEach((evt) => {
      window.addEventListener(evt, handleUserActivity, { passive: true });
    });

    return () => {
      clearTimers();
      trackedEvents.forEach((evt) => {
        window.removeEventListener(evt, handleUserActivity);
      });
    };
  }, [clearTimers, enabled, resetIdleTimer]);

  return {
    isWarningOpen,
    remainingSeconds,
    resetIdleTimer: () => resetIdleTimer(true),
    confirmLogout: () => triggerLogout('user_confirmed'),
  };
}
