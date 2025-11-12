// HCT Voice Agent - Audio-Reactive Logo + Live Captions
const API = window.location.origin;
const SESSION_ID = 'session_' + Date.now();

// State
const state = {
    mode: null,
    isListening: false,
    recognition: null,
    audioContext: null,
    analyser: null,
    currentAudio: null,
    animationFrame: null
};

// Elements
let loadingScreen1, loadingScreen2, mainMenu;
let voiceMode, textMode;
let micButton, statusText, liveCaption;
let messageInput, chatArea, welcomeMessage;
let logoWrapper, logo, cancelButton, thinkingIndicator;

// Wait for DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 HCT Voice Agent starting...');

    loadingScreen1 = document.getElementById('loadingScreen1');
    loadingScreen2 = document.getElementById('loadingScreen2');
    mainMenu = document.getElementById('mainMenu');
    voiceMode = document.getElementById('voiceMode');
    textMode = document.getElementById('textMode');
    micButton = document.getElementById('micButton');
    statusText = document.getElementById('statusText');
    liveCaption = document.getElementById('liveCaption');
    messageInput = document.getElementById('messageInput');
    chatArea = document.getElementById('chatArea');
    welcomeMessage = document.getElementById('welcomeMessage');
    logoWrapper = document.getElementById('logoWrapper');
    logo = document.getElementById('hctLogo');
    cancelButton = document.getElementById('cancelButton');
    thinkingIndicator = document.getElementById('thinkingIndicator');

    setupEvents();
    initSpeech();
    initAudioContext();
    startLoadingSequence();
});

function startLoadingSequence() {
    console.log('📺 Starting loading sequence...');

    setTimeout(() => {
        console.log('📺 Screen 1 → Screen 2');
        loadingScreen1.classList.remove('active');
        loadingScreen2.classList.add('active');

        setTimeout(() => {
            console.log('📺 Screen 2 → Main Menu');
            loadingScreen2.classList.remove('active');
            mainMenu.classList.add('active');
            console.log('✅ Loading complete');
        }, 300);
    }, 300);
}

function showMainMenu() {
    console.log('🏠 Returning to main menu');

    if (voiceMode) voiceMode.classList.remove('active');
    if (textMode) textMode.classList.remove('active');
    if (mainMenu) mainMenu.classList.add('active');

    // Clear animations and captions
    if (logoWrapper) {
        logoWrapper.classList.remove('thinking', 'speaking');
    }
    if (liveCaption) {
        liveCaption.classList.remove('active');
        liveCaption.textContent = '';
    }
    stopAudioVisualization();

    state.mode = null;
}

function switchToMode(mode) {
    console.log('🔄 Switching to:', mode);

    if (mainMenu) mainMenu.classList.remove('active');

    if (mode === 'voice' && voiceMode) {
        voiceMode.classList.add('active');
        state.mode = 'voice';
        console.log('✅ Voice mode activated');
    } else if (mode === 'text' && textMode) {
        textMode.classList.add('active');
        state.mode = 'text';
        console.log('✅ Text mode activated');
    }
}

// Initialize Audio Context for audio-reactive visualization
function initAudioContext() {
    try {
        state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        state.analyser = state.audioContext.createAnalyser();
        state.analyser.fftSize = 256;
        console.log('✅ Audio context initialized');
    } catch (e) {
        console.warn('⚠️ Audio context not available:', e);
    }
}

function initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('⚠️ Speech recognition not supported');
        return;
    }

    state.recognition = new SpeechRecognition();
    state.recognition.continuous = false;
    state.recognition.interimResults = false;
    state.recognition.lang = 'en-US';

    state.recognition.onstart = () => {
        console.log('🎤 Listening...');
        statusText.textContent = 'Listening...';
        micButton.classList.add('recording');
    };

    state.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('📝 Heard:', transcript);
        getAIResponse(transcript);
    };

    state.recognition.onend = () => {
        console.log('🎤 Stopped listening');
        micButton.classList.remove('recording');
        state.isListening = false;
    };

    state.recognition.onerror = (event) => {
        console.error('❌ Speech error:', event.error);
        statusText.textContent = 'Error - try again';
        micButton.classList.remove('recording');
        logoWrapper.classList.remove('thinking', 'speaking');
        state.isListening = false;
    };
}

function toggleListening() {
    if (state.isListening) {
        state.recognition.stop();
        state.isListening = false;
    } else {
        state.recognition.start();
        state.isListening = true;
    }
}

// Get AI Response
async function getAIResponse(text) {
    console.log('💬 Getting response for:', text);
    statusText.textContent = 'Thinking...';

    // Show thinking animation
    logoWrapper.classList.add('thinking');

    try {
        const response = await fetch(`${API}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                session_id: SESSION_ID
            })
        });

        if (!response.ok) throw new Error('Chat failed');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.content) {
                            fullResponse += parsed.content;
                        }
                    } catch (e) { }
                }
            }
        }

        console.log('✅ Got response:', fullResponse);
        speak(fullResponse);

    } catch (error) {
        console.error('❌ Error:', error);
        statusText.textContent = 'Error - try again';
        logoWrapper.classList.remove('thinking', 'speaking');
    }
}

// Speak with audio-reactive logo pulse and live captions
async function speak(text) {
    console.log('🔊 Speaking with live captions');
    statusText.textContent = 'Speaking...';

    // Switch to speaking mode
    logoWrapper.classList.remove('thinking');
    logoWrapper.classList.add('speaking');

    try {
        const response = await fetch(`${API}/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice: 'nova'
            })
        });

        if (!response.ok) throw new Error('TTS failed');

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        state.currentAudio = audio;

        // Connect audio to analyser for visualization
        if (state.audioContext && state.analyser) {
            const source = state.audioContext.createMediaElementSource(audio);
            source.connect(state.analyser);
            state.analyser.connect(state.audioContext.destination);
        }

        audio.onloadedmetadata = () => {
            console.log('✅ Audio ready');
            audio.play();

            // Start audio-reactive visualization
            startAudioVisualization();

            // Show live captions
            showLiveCaptions(text, audio.duration);
        };

        audio.onended = () => {
            console.log('✅ Finished speaking');
            statusText.textContent = 'Click to start';
            logoWrapper.classList.remove('speaking');
            liveCaption.classList.remove('active');
            stopAudioVisualization();
            URL.revokeObjectURL(audioUrl);
            state.currentAudio = null;
        };

        audio.onerror = (e) => {
            console.error('❌ Audio error:', e);
            statusText.textContent = 'Click to start';
            logoWrapper.classList.remove('speaking');
            liveCaption.classList.remove('active');
            stopAudioVisualization();
            URL.revokeObjectURL(audioUrl);
        };

    } catch (error) {
        console.error('❌ TTS error:', error);
        statusText.textContent = 'Click to start';
        logoWrapper.classList.remove('speaking');
        liveCaption.classList.remove('active');
    }
}

// Audio-reactive logo pulsing (synced with speech volume)
function startAudioVisualization() {
    if (!state.analyser) return;

    const dataArray = new Uint8Array(state.analyser.frequencyBinCount);

    function animate() {
        state.animationFrame = requestAnimationFrame(animate);

        state.analyser.getByteFrequencyData(dataArray);

        // Calculate average volume
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

        // Map volume to scale (1.0 to 1.12)
        const scale = 1 + (average / 255) * 0.12;

        // Apply scale to logo
        if (logo) {
            logo.style.transform = `scale(${scale})`;
        }
    }

    animate();
    console.log('🎵 Audio visualization started');
}

function stopAudioVisualization() {
    if (state.animationFrame) {
        cancelAnimationFrame(state.animationFrame);
        state.animationFrame = null;
    }

    // Reset logo scale
    if (logo) {
        logo.style.transform = 'scale(1)';
    }

    console.log('⏹️ Audio visualization stopped');
}

// Live captions - show text as it's being spoken (like live captions)
function showLiveCaptions(text, duration) {
    liveCaption.classList.add('active');

    // Split text into words
    const words = text.split(' ');
    const msPerWord = (duration * 1000) / words.length;

    let currentIndex = 0;
    liveCaption.textContent = '';

    const interval = setInterval(() => {
        if (currentIndex >= words.length) {
            clearInterval(interval);
            return;
        }

        // Add next word
        liveCaption.textContent += (currentIndex > 0 ? ' ' : '') + words[currentIndex];
        currentIndex++;

    }, msPerWord);

    console.log('💬 Live captions started');
}

// Text mode
function sendTextMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    console.log('📤 Sending:', text);
    messageInput.value = '';

    addMessage('user', text);
    getTextResponse(text);
}

async function getTextResponse(text) {
    if (thinkingIndicator) {
        thinkingIndicator.classList.add('visible');
    }

    try {
        const response = await fetch(`${API}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                session_id: SESSION_ID
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.content) {
                            fullResponse += parsed.content;
                        }
                    } catch (e) { }
                }
            }
        }

        if (thinkingIndicator) {
            thinkingIndicator.classList.remove('visible');
        }

        addMessage('assistant', fullResponse);

    } catch (error) {
        console.error('❌ Error:', error);

        if (thinkingIndicator) {
            thinkingIndicator.classList.remove('visible');
        }

        addMessage('assistant', 'Sorry, I encountered an error.');
    }
}

function addMessage(role, content) {
    if (welcomeMessage) {
        welcomeMessage.classList.add('hidden');
    }

    const div = document.createElement('div');
    div.className = `chat-message ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;

    // Create action buttons
    const actions = document.createElement('div');
    actions.className = 'message-actions';

    if (role === 'user') {
        // User messages: Copy + Edit
        actions.innerHTML = `
            <button class="message-action-btn copy-btn" title="Copy" aria-label="Copy message">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <button class="message-action-btn edit-btn" title="Edit" aria-label="Edit message">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `;
    } else {
        // Assistant messages: Copy + Thumbs Up + Thumbs Down
        actions.innerHTML = `
            <button class="message-action-btn copy-btn" title="Copy" aria-label="Copy message">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <button class="message-action-btn thumb thumb-up" title="Good response" aria-label="Thumbs up">
                <svg width="18" height="18" viewBox="0 0 24 24">
                    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
                </svg>
            </button>
            <button class="message-action-btn thumb thumb-down" title="Bad response" aria-label="Thumbs down">
                <svg width="18" height="18" viewBox="0 0 24 24">
                    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
                </svg>
            </button>
        `;
    }

    // Add event listeners to action buttons
    const copyBtn = actions.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.onclick = (e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(content).then(() => {
                console.log('📋 Message copied');
                // Show brief "Copied!" feedback
                copyBtn.title = 'Copied!';
                setTimeout(() => copyBtn.title = 'Copy', 1000);
            });
        };
    }

    const editBtn = actions.querySelector('.edit-btn');
    if (editBtn) {
        editBtn.onclick = (e) => {
            e.stopPropagation();
            console.log('✏️ Edit message:', content);
            // Put message back in input for editing
            if (messageInput) {
                messageInput.value = content;
                messageInput.focus();
            }
        };
    }

    const thumbUpBtn = actions.querySelector('.thumb-up');
    if (thumbUpBtn) {
        thumbUpBtn.onclick = (e) => {
            e.stopPropagation();
            console.log('👍 Good response');
            thumbUpBtn.style.opacity = '1';
            // Optional: Send feedback to backend
        };
    }

    const thumbDownBtn = actions.querySelector('.thumb-down');
    if (thumbDownBtn) {
        thumbDownBtn.onclick = (e) => {
            e.stopPropagation();
            console.log('👎 Bad response');
            thumbDownBtn.style.opacity = '1';
            // Optional: Send feedback to backend
        };
    }

    div.appendChild(bubble);
    div.appendChild(actions);
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Setup events
function setupEvents() {
    const selectTextBtn = document.getElementById('selectTextMode');
    const selectVoiceBtn = document.getElementById('selectVoiceMode');

    if (selectTextBtn) {
        selectTextBtn.onclick = () => {
            console.log('📘 Text mode selected');
            switchToMode('text');
        };
    }

    if (selectVoiceBtn) {
        selectVoiceBtn.onclick = () => {
            console.log('📘 Voice mode selected');
            switchToMode('voice');
        };
    }

    const closeVoice = document.getElementById('closeVoice');
    const closeText = document.getElementById('closeText');

    if (closeVoice) {
        closeVoice.onclick = () => {
            console.log('📘 Close voice mode');
            showMainMenu();
        };
    }

    if (closeText) {
        closeText.onclick = () => {
            console.log('📘 Close text mode');
            showMainMenu();
        };
    }

    if (micButton) {
        micButton.onclick = toggleListening;
    }

    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.onclick = sendTextMessage;
    }

    if (messageInput) {
        messageInput.onkeypress = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendTextMessage();
            }
        };
    }

    if (cancelButton) {
        cancelButton.onclick = () => {
            console.log('❌ Cancel');
            if (state.recognition && state.isListening) {
                state.recognition.stop();
            }
            if (state.currentAudio) {
                state.currentAudio.pause();
                state.currentAudio = null;
            }
        };
    }
}

console.log('✅ HCT Voice Agent script loaded');