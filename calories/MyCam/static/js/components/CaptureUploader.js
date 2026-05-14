window.CaptureUploader = {
  template: `
    <div class="row g-4">
      <div class="col-lg-6">
        <div class="mc-card">
          <h5 class="mc-card__title"><i class="bi bi-camera-video me-1"></i>Use camera</h5>
          <div class="mc-camera mb-3">
            <video ref="video" autoplay playsinline muted v-show="streaming"></video>
            <img v-if="!streaming && snapshot" :src="snapshot" />
            <div v-if="!streaming && !snapshot" class="d-flex h-100 align-items-center justify-content-center text-secondary">
              <span><i class="bi bi-camera-video-off"></i> Camera not started</span>
            </div>
          </div>
          <div class="d-flex flex-wrap gap-2">
            <button class="mc-btn-primary" v-if="!streaming" @click="startCamera">
              <i class="bi bi-play-circle"></i> Start camera
            </button>
            <button class="mc-btn-primary" v-if="streaming" @click="capture" :disabled="loading">
              <i class="bi bi-camera"></i> Take photo
            </button>
            <button class="btn btn-outline-secondary rounded-pill" v-if="streaming" @click="stopCamera">Close</button>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="mc-card">
          <h5 class="mc-card__title"><i class="bi bi-cloud-upload me-1"></i>Upload photo</h5>
          <div class="mc-drop" :class="{dragover}"
               @dragover.prevent="dragover=true"
               @dragleave.prevent="dragover=false"
               @drop.prevent="onDrop">
            <div v-if="!preview">
              <i class="bi bi-image" style="font-size:2rem"></i>
              <p class="mt-2 mb-1">Drop an image here, or click the button below</p>
              <small class="text-muted">Supports JPG / PNG / WEBP, max 8 MB</small>
            </div>
            <img v-else :src="preview" class="mc-drop__preview" />
          </div>
          <input type="file" ref="file" class="d-none" accept="image/*" @change="onPick" />
          <div class="d-flex flex-wrap gap-2 mt-3">
            <button class="btn btn-outline-primary rounded-pill" @click="$refs.file.click()">
              <i class="bi bi-folder2-open"></i> Choose file
            </button>
            <button class="mc-btn-primary" :disabled="!file || loading" @click="uploadFile">
              <span v-if="loading"><span class="spinner-border spinner-border-sm me-1"></span>Analysing…</span>
              <span v-else><i class="bi bi-stars"></i> Start analysis</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      streaming: false, stream: null,
      file: null, preview: null, snapshot: null,
      dragover: false, loading: false
    };
  },
  beforeUnmount() { this.stopCamera(); },
  methods: {
    async startCamera() {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        this.streaming = true;
        await this.$nextTick();
        this.$refs.video.srcObject = this.stream;
      } catch (e) {
        MC.notify('error', 'Could not start camera', e.message);
      }
    },
    stopCamera() {
      this.stream?.getTracks().forEach(t => t.stop());
      this.stream = null; this.streaming = false;
    },
    async capture() {
      const v = this.$refs.video;
      const canvas = document.createElement('canvas');
      canvas.width = v.videoWidth; canvas.height = v.videoHeight;
      canvas.getContext('2d').drawImage(v, 0, 0);
      const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.9));
      this.snapshot = URL.createObjectURL(blob);
      this.stopCamera();
      await this._send(blob, 'capture.jpg');
    },
    onPick(e) {
      const f = e.target.files[0] || null;
      this._setFile(f);
    },
    onDrop(e) {
      this.dragover = false;
      const f = e.dataTransfer.files[0];
      if (f) this._setFile(f);
    },
    _setFile(f) {
      this.file = f;
      this.preview = f ? URL.createObjectURL(f) : null;
    },
    async uploadFile() { await this._send(this.file, this.file.name); },
    async _send(blob, name) {
      this.loading = true;
      try {
        const fd = new FormData();
        fd.append('image', blob, name);
        const { data } = await axios.post('/api/analyze', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        await Swal.fire({
          icon: 'success', title: 'Analysis complete',
          text: data.data.summary || 'Analysis ready',
          confirmButtonText: 'View details'
        });
        location.href = '/history/' + data.data.id;
      } catch (e) {
        Swal.fire({ icon: 'error', title: 'Analysis failed', text: MC.errorOf(e) });
      } finally {
        this.loading = false;
      }
    }
  }
};
