<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	// This type should match the Sticker model in the backend
	type Sticker = {
		id: string;
		src: string;
		x: number;
		y: number;
		rotation: number;
		scale: number;
	};

	export let sticker: Sticker;
	export let editing: boolean;
	export let polaroidElement: HTMLElement; // The DOM element of the polaroid container

	const dispatch = createEventDispatcher();

	let dragging = false;
	let imgElement: HTMLImageElement;

	// We store the offset from the pointer to the element's top-left corner
	let offsetX: number;
	let offsetY: number;

	function handlePointerDown(event: PointerEvent) {
		if (!editing || !polaroidElement) return;

		event.preventDefault();
		dragging = true;

		// Capture pointer events so we get them even if the cursor leaves the element
		imgElement.setPointerCapture(event.pointerId);

		// Calculate the initial offset of the pointer from the sticker's top-left corner
		const stickerRect = imgElement.getBoundingClientRect();
		offsetX = event.clientX - stickerRect.left;
		offsetY = event.clientY - stickerRect.top;

		// Add listeners to the window to handle dragging and release
		window.addEventListener('pointermove', handlePointerMove);
		window.addEventListener('pointerup', handlePointerUp);
	}

	function handlePointerMove(event: PointerEvent) {
		if (!dragging) return;

		event.preventDefault();

		// Get the bounding box of the parent polaroid
		const polaroidRect = polaroidElement.getBoundingClientRect();

		// Calculate the new X and Y based on pointer position, parent position, and initial offset
		const newX = event.clientX - polaroidRect.left - offsetX;
		const newY = event.clientY - polaroidRect.top - offsetY;

		// Dispatch an 'update' event to notify the parent component of the new position
		dispatch('update', {
			id: sticker.id,
			x: newX,
			y: newY
		});
	}

	function handlePointerUp(event: PointerEvent) {
		if (!dragging) return;
		dragging = false;

		// Release the pointer capture
		imgElement.releasePointerCapture(event.pointerId);

		// Clean up the window event listeners
		window.removeEventListener('pointermove', handlePointerMove);
		window.removeEventListener('pointerup', handlePointerUp);

		// Notify parent that dragging has finished (e.g., for an autosave)
		dispatch('dragend');
	}

	// Reactive style declaration that updates whenever sticker props or dragging state change
	$: style = `
    position: absolute;
    top: ${sticker.y}px;
    left: ${sticker.x}px;
    touch-action: none; /* Prevents page scrolling on touch devices */
    user-select: none; /* Prevents selecting the image while dragging */
    z-index: ${dragging ? 1000 : 0};
    ${editing ? 'cursor: grab;' : 'cursor: default;'}
    ${dragging ? 'cursor: grabbing;' : ''}
  `;
</script>

<img
	bind:this={imgElement}
	src={sticker.src}
	alt="A draggable sticker"
	class="object-contain z-99 transform scale-40"
	{style}
	on:pointerdown={handlePointerDown}
	draggable="false"
/>
