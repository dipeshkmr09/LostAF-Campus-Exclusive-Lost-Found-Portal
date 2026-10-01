// ============================================================
// AUTH.JS — Firebase Authentication (modular SDK v12)
// This file runs as an ES module. It wires Firebase to the
// UI helper functions defined in script.js (global scope).
// ============================================================

import { initializeApp }                          from "https://www.gstatic.com/firebasejs/12.10.0/firebase-app.js";
import { getAnalytics }                           from "https://www.gstatic.com/firebasejs/12.10.0/firebase-analytics.js";
import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    signOut,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.10.0/firebase-auth.js";

// ── Firebase project config ─────────────────────────────────
const firebaseConfig = {
    apiKey:            "AIzaSyA2-_7YRyui4tcNYr9LhZAZlFhL9qMN1K0",
    authDomain:        "lostaf-auth.firebaseapp.com",
    projectId:         "lostaf-auth",
    storageBucket:     "lostaf-auth.firebasestorage.app",
    messagingSenderId: "335092192093",
    appId:             "1:335092192093:web:eae66d63b172ed61120eb4",
    measurementId:     "G-273RGRK1QN"
};

// ── Allowed email domain ─────────────────────────────────────
const ALLOWED_DOMAIN = 'cgu-odisha.ac.in';

// ── Initialize ───────────────────────────────────────────────
const app      = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth     = getAuth(app);
const provider = new GoogleAuthProvider();

// Hint Google account picker to surface college accounts first
provider.setCustomParameters({ hd: ALLOWED_DOMAIN });

// ── Auth state observer ──────────────────────────────────────
// When a user signs in or out (including page reload restoring
// a previous session), this fires and updates the entire UI.
onAuthStateChanged(auth, async (user) => {
    if (user) {
        const domain = user.email.split('@')[1];

        // Domain guard — sign out and surface error immediately
        if (domain !== ALLOWED_DOMAIN) {
            await signOut(auth);
            if (typeof window.showToast === 'function') {
                window.showToast(
                    'Only college email accounts are allowed to use this portal.',
                    'info'
                );
            }
            window.currentUser    = null;
            window.firebaseIdToken = null;
            if (typeof window.updateAuthUI === 'function') window.updateAuthUI(false, null);
            return;
        }

        // Valid domain — get fresh ID token and sync user to DB
        const token = await user.getIdToken();
        window.currentUser     = user;
        window.firebaseIdToken = token;

        if (typeof window.syncUserToDB === 'function') window.syncUserToDB(user, token);
        if (typeof window.updateAuthUI === 'function')  window.updateAuthUI(true, user);
        if (typeof window.closeAuthModal === 'function') window.closeAuthModal();

    } else {
        window.currentUser     = null;
        window.firebaseIdToken = null;
        if (typeof window.updateAuthUI === 'function') window.updateAuthUI(false, null);
    }
});

// ── Exposed to global scope (called by onclick handlers) ─────

window.loginWithGoogle = async function () {
    try {
        await signInWithPopup(auth, provider);
    } catch (err) {
        const code = err.code || '';
        console.error('[Auth] signInWithPopup error:', code, err.message);

        // Silent — user just closed the popup
        if (code === 'auth/popup-closed-by-user' ||
            code === 'auth/cancelled-popup-request') return;

        if (typeof window.showToast === 'function') {
            window.showToast('Login failed. Please try again.', 'info');
        }
    }
};

window.logout = async function () {
    await signOut(auth);
    if (typeof window.showToast === 'function') {
        window.showToast('Signed out successfully.', 'success');
    }
    if (typeof window.navigate === 'function') window.navigate('landing');
};
