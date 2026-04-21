const activateBtn = document.getElementById('activate-sos');
const mediaToggle = document.getElementById('media-toggle');
const mediaControls = document.getElementById('media-controls');
const chevron = document.getElementById('chevron');
const emergencyText = document.getElementById('emergency-text');
const video = document.getElementById('camera-stream');
const canvas = document.getElementById('capture-canvas');
const proofBtn = document.getElementById('proof-btn');
const recordBtn = document.getElementById('record-btn');
const visualizerBar = document.getElementById('visualizer-bar');
const statusMsg = document.getElementById('status-message');
const batteryStatus = document.getElementById('battery-status');

let currentImageB64 = null;
let currentAudioB64 = null;
let locationData = { lat: 0, lng: 0 };
let mediaStream = null;
let mediaRecorder = null;
let audioChunks = [];

// Battery Sync (15% Threshold)
if ('getBattery' in navigator) {
    navigator.getBattery().then(battery => {
        const checkBattery = () => {
            const level = Math.round(battery.level * 100);
            batteryStatus.textContent = `BAT: ${level}%`;
            document.body.classList.toggle('low-power', battery.level < 0.15);
        };
        checkBattery();
        battery.addEventListener('levelchange', checkBattery);
    });
}

// Media Logic (Lazy Init)
mediaToggle.addEventListener('click', async () => {
    const isHidden = mediaControls.classList.contains('hidden');
    mediaControls.classList.toggle('hidden');
    chevron.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';

    if (isHidden && !mediaStream) {
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = mediaStream;
            setupAudioRecorder();
        } catch (e) {
            statusMsg.textContent = "PERMISSION DENIED: CAMERA/MIC";
        }
    }
});

function setupAudioRecorder() {
    mediaRecorder = new MediaRecorder(mediaStream);
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
            currentAudioB64 = reader.result.split(',')[1];
            statusMsg.textContent = "VOICE SIGNATURE CAPTURED";
            recordBtn.classList.add('bg-pink-600', 'text-white');
        };
        audioChunks = [];
    };
}

// Geo Tracking
navigator.geolocation.getCurrentPosition(
    pos => { locationData = { lat: pos.coords.latitude, lng: pos.coords.longitude }; },
    err => {
        const landmark = prompt("GPS DENIED. Please enter nearest landmark:");
        locationData.landmark = landmark || "Unknown";
    }
);

// Proof Capture
proofBtn.addEventListener('click', () => {
    if (!video.videoWidth) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    currentImageB64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
    statusMsg.textContent = "PHOTO INTEL CAPTURED";
    proofBtn.classList.add('bg-pink-600', 'text-white');
});

// Audio Capture
recordBtn.addEventListener('mousedown', () => {
    if (!mediaRecorder) return;
    audioChunks = [];
    mediaRecorder.start();
    visualizerBar.style.width = '100%';
    statusMsg.textContent = "RECORDING VOICE...";
});

recordBtn.addEventListener('mouseup', () => {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') return;
    mediaRecorder.stop();
    visualizerBar.style.width = '0%';
});

// SOS Submission (IndexedDB Fallback)
async function saveToVault(payload) {
    return new Promise((resolve) => {
        const request = indexedDB.open("InstantDRSVault", 1);
        request.onupgradeneeded = e => e.target.result.createObjectStore("sos", { autoIncrement: true });
        request.onsuccess = e => {
            const db = e.target.result;
            const tx = db.transaction("sos", "readwrite");
            tx.objectStore("sos").add(payload);
            tx.oncomplete = () => resolve();
        };
    });
}

activateBtn.addEventListener('click', async () => {
    if (activateBtn.disabled) return;
    const text = emergencyText.value.trim();
    if (!text) { statusMsg.textContent = "REQUIRED: INCIDENT INTEL"; return; }

    activateBtn.disabled = true;
    activateBtn.textContent = "TRANSMITTING...";

    const payload = {
        text: text,
        image_b64: currentImageB64,
        audio_b64: currentAudioB64,
        lat: locationData.lat,
        lng: locationData.lng,
        landmark: locationData.landmark,
        time: Math.floor(Date.now() / 1000)
    };

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 20000);

        const response = await fetch('/triage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        clearTimeout(timeout);

        if (response.ok) {
            window.location.href = '/submitted.html';
        } else {
            throw new Error();
        }
    } catch (e) {
        statusMsg.textContent = "DEAD ZONE DETECTED: SAVED TO VAULT";
        await saveToVault(payload);
        activateBtn.textContent = "RETRY";
        activateBtn.disabled = false;
    }
});


