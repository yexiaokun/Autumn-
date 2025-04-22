// image-resize.js
(function () {
    const Quill = window.Quill;
    if (!Quill) {
        console.error('Quill is not defined. Please make sure Quill is loaded before this module.');
        return;
    }

    const Delta = Quill.import('delta');

    class ImageResize {
        constructor(quill, options = {}) {
            this.quill = quill;
            this.options = options;
            this.init();
        }
    
        init() {
            this.quill.root.addEventListener('click', (event) => {
                if (event.target.tagName === 'IMG') {
                    this.showResizer(event.target);
                }
            });
        }
    
        showResizer(img) {
            if (!this.resizer) {
                this.resizer = document.createElement('div');
                this.resizer.classList.add('ql-image-resize');
                document.body.appendChild(this.resizer);
    
                const handleTopLeft = this.createHandle('top-left');
                const handleTopRight = this.createHandle('top-right');
                const handleBottomLeft = this.createHandle('bottom-left');
                const handleBottomRight = this.createHandle('bottom-right');
    
                this.resizer.appendChild(handleTopLeft);
                this.resizer.appendChild(handleTopRight);
                this.resizer.appendChild(handleBottomLeft);
                this.resizer.appendChild(handleBottomRight);
            }
    
            const rect = img.getBoundingClientRect();
            this.resizer.style.left = rect.left + window.pageXOffset + 'px';
            this.resizer.style.top = rect.top + window.pageYOffset + 'px';
            this.resizer.style.width = rect.width + 'px';
            this.resizer.style.height = rect.height + 'px';
            this.resizer.style.display = 'block';
    
            this.currentImage = img;
        }
    
        createHandle(position) {
            const handle = document.createElement('div');
            handle.classList.add('ql-image-resize-handle', `ql-image-resize-handle-${position}`);
            const startResizeHandler = (event) => {
                event.preventDefault();
                console.log('Handle mousedown event triggered');
                this.startResize(event, position);
            };
            handle.addEventListener('mousedown', startResizeHandler);
            return handle;
        }
    
        startResize(event, position) {
            this.startX = event.clientX;
            this.startY = event.clientY;
            this.startWidth = this.currentImage.width;
            this.startHeight = this.currentImage.height;
            this.resizePosition = position;
    
            console.log('Start resize event triggered');
            this.onMouseMoveHandler = this.onMouseMove.bind(this);
            this.onMouseUpHandler = this.onMouseUp.bind(this);
            document.addEventListener('mousemove', this.onMouseMoveHandler);
            document.addEventListener('mouseup', this.onMouseUpHandler);
        }
    
        onMouseMove(event) {
            const dx = event.clientX - this.startX;
            const dy = event.clientY - this.startY;
    
            let newWidth, newHeight;
            switch (this.resizePosition) {
                case 'top-left':
                    newWidth = this.startWidth - dx;
                    newHeight = this.startHeight - dy;
                    break;
                case 'top-right':
                    newWidth = this.startWidth + dx;
                    newHeight = this.startHeight - dy;
                    break;
                case 'bottom-left':
                    newWidth = this.startWidth - dx;
                    newHeight = this.startHeight + dy;
                    break;
                case 'bottom-right':
                    newWidth = this.startWidth + dx;
                    newHeight = this.startHeight + dy;
                    break;
            }
    
            // 保持图片比例
            if (this.options.keepRatio) {
                const ratio = this.startWidth / this.startHeight;
                if (Math.abs(dx) > Math.abs(dy)) {
                    newHeight = newWidth / ratio;
                } else {
                    newWidth = newHeight * ratio;
                }
            }
    
            this.currentImage.style.width = newWidth + 'px';
            this.currentImage.style.height = newHeight + 'px';
    
            const rect = this.currentImage.getBoundingClientRect();
            this.resizer.style.left = rect.left + window.pageXOffset + 'px';
            this.resizer.style.top = rect.top + window.pageYOffset + 'px';
            this.resizer.style.width = rect.width + 'px';
            this.resizer.style.height = rect.height + 'px';
    
            console.log('New width:', newWidth, 'New height:', newHeight);
        }
    
        onMouseUp() {
            document.removeEventListener('mousemove', this.onMouseMoveHandler);
            document.removeEventListener('mouseup', this.onMouseUpHandler);
    
            let index = 0;
            const delta = this.quill.getContents();
            let found = false;
            delta.ops.forEach((op) => {
                if (!found) {
                    if (op.insert && typeof op.insert === 'object' && op.insert.image === this.currentImage.src) {
                        found = true;
                    } else if (typeof op.insert === 'string') {
                        index += op.insert.length;
                    } else if (op.insert && typeof op.insert === 'object') {
                        index++;
                    }
                }
            });
    
            if (found) {
                const newDelta = new Delta()
                    .retain(index)
                    .delete(1)
                    .insert({ image: this.currentImage.src }, { width: this.currentImage.style.width, height: this.currentImage.style.height });
                console.log('Index:', index, 'Delta:', newDelta);
                this.quill.updateContents(newDelta);
            }
            this.resizer.style.display = 'none';
        }
    }
    

    Quill.register('modules/imageResize', ImageResize);
})();