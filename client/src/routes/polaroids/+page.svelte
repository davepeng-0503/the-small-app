<script lang="ts">
	import { onMount } from 'svelte';
	import DraggableSticker from '$lib/components/DraggableSticker.svelte';

	// Matches backend Pydantic models
	type Sticker = {
		id: string;
		src: string;
		x: number;
		y: number;
		rotation: number;
		scale: number;
	};

	type Polaroid = {
		id: string;
		src: string;
		createdAt: Date;
		description: string;
		stickers: Sticker[];
		editing: boolean;
	};

	const API_URL = 'http://localhost:8001';
	let polaroids: Polaroid[] = [];
	let polaroidElements: { [id: string]: HTMLElement } = {};

	onMount(async () => {
		try {
			const response = await fetch(`${API_URL}/polaroids`);
			if (!response.ok) {
				throw new Error('Failed to fetch polaroids');
			}
			const data = await response.json();
			polaroids = data.map((p: any) => ({
				...p,
				src: `${p.src}`,
				createdAt: new Date(p.createdAt),
				editing: false,
				stickers:
					p.stickers?.map((s: any) => ({
						...s,
						src: `${s.src}`
					})) || []
			}));
		} catch (error) {
			console.error('Error fetching polaroids:', error);
		}
	});

	async function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			const file = target.files[0];
			const reader = new FileReader();
			reader.onload = async (e) => {
				if (typeof e.target?.result === 'string') {
					try {
						const response = await fetch(`${API_URL}/polaroids`, {
							method: 'POST',
							headers: {
								'Content-Type': 'application/json'
							},
							body: JSON.stringify({ image_base64: e.target.result })
						});

						if (!response.ok) {
							throw new Error('Failed to upload polaroid');
						}

						const newPolaroidData = await response.json();
						const newPolaroid: Polaroid = {
							...newPolaroidData,
							src: `${newPolaroidData.src}`,
							createdAt: new Date(newPolaroidData.createdAt),
							editing: true, // Start in editing mode
							stickers:
								newPolaroidData.stickers?.map((s: any) => ({
									...s,
									src: `${s.src}`
								})) || []
						};
						polaroids = [...polaroids, newPolaroid];
					} catch (error) {
						console.error('Error uploading polaroid:', error);
						alert('Failed to upload polaroid. See console for details.');
					}
				}
			};
			reader.readAsDataURL(file);
		}
	}

	function toggleEdit(id: string) {
		polaroids = polaroids.map((p) => (p.id === id ? { ...p, editing: !p.editing } : p));
	}

	async function saveChanges(polaroid: Polaroid) {
		try {
			// Strip the API_URL from sticker sources before sending to the backend
			const stickersToSave = polaroid.stickers.map((s) => ({
				...s,
			}));

			const response = await fetch(`${API_URL}/polaroids/${polaroid.id}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					description: polaroid.description,
					createdAt: polaroid.createdAt.toISOString(),
					stickers: stickersToSave
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to save polaroid');
			}
			// No longer toggles edit mode, allowing for autosave on drag
		} catch (error) {
			console.error('Error saving polaroid:', error);
			alert(`Error: ${error}`);
		}
	}

	async function handleSaveAndExit(polaroid: Polaroid) {
		await saveChanges(polaroid);
		toggleEdit(polaroid.id);
	}

	async function deletePolaroid(id: string) {
		if (!confirm('Are you sure you want to delete this polaroid memory?')) {
			return;
		}

		try {
			const response = await fetch(`${API_URL}/polaroids/${id}`, {
				method: 'DELETE'
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ detail: 'Failed to delete polaroid' }));
				throw new Error(errorData.detail);
			}

			polaroids = polaroids.filter((p) => p.id !== id);
		} catch (error) {
			console.error('Error deleting polaroid:', error);
			alert(`Error: ${error}`);
		}
	}

	function handleStickerUpdate(event: CustomEvent, polaroidId: string) {
		const { id: stickerId, x, y } = event.detail;

		polaroids = polaroids.map((p) => {
			if (p.id === polaroidId) {
				const newStickers = p.stickers.map((s) => {
					if (s.id === stickerId) {
						return { ...s, x, y };
					}
					return s;
				});
				return { ...p, stickers: newStickers };
			}
			return p;
		});
	}

	function formatDateForInput(date: Date): string {
		const d = new Date(date);
		const year = d.getFullYear();
		let month = '' + (d.getMonth() + 1);
		let day = '' + d.getDate();

		if (month.length < 2) month = '0' + month;
		if (day.length < 2) day = '0' + day;

		return [year, month, day].join('-');
	}

	function handleDateChange(event: Event, polaroidId: string) {
		const target = event.target as HTMLInputElement;
		const [year, month, day] = target.value.split('-').map(Number);

		polaroids = polaroids.map((p) => {
			if (p.id === polaroidId) {
				return { ...p, createdAt: new Date(year, month - 1, day) };
			}
			return p;
		});
	}
</script>

<div class="p-6 min-h-full">
	<h1 class="text-4xl text-rose-500 font-bold mb-8 text-center">Polaroid Memories</h1>

	<div class="mb-8 text-center">
		<label
			for="file-upload"
			class="cursor-pointer bg-rose-400 hover:bg-rose-500 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-transform transform hover:scale-105"
		>
			+ Add a Polaroid
		</label>
		<input
			id="file-upload"
			type="file"
			class="hidden"
			on:change={handleFileUpload}
			accept="image/*"
		/>
	</div>

	{#if polaroids.length === 0}
		<div class="text-center py-20">
			<p class="text-gray-500 text-lg">Upload a photo to start creating your polaroid wall!</p>
			<div class="text-6xl mt-4">📸</div>
		</div>
	{/if}

	<div
		class="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4"
	>
		{#each polaroids.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()) as polaroid (polaroid.id)}
			<div
				class="bg-white p-4 shadow-lg rounded-sm flex flex-col relative group transform hover:-translate-y-2 transition-transform duration-300"
			>
				<div
					class="absolute top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2"
				>
					{#if polaroid.editing}
						<button
							on:click={() => handleSaveAndExit(polaroid)}
							class="bg-rose-400 hover:bg-rose-500 text-white font-bold py-1 px-3 rounded-full shadow-lg text-sm"
						>
							Save
						</button>
					{:else}
						<button
							on:click={() => toggleEdit(polaroid.id)}
							class="bg-white/80 text-gray-600 hover:text-gray-900 p-2 rounded-full shadow-md z-99"
							aria-label="Edit polaroid"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
								/>
							</svg>
						</button>
						<button
							on:click={() => deletePolaroid(polaroid.id)}
							class="bg-white/80 text-red-500 hover:text-red-700 p-2 rounded-full shadow-md"
							aria-label="Delete polaroid"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="2"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
								/>
							</svg>
						</button>
					{/if}
				</div>

				<div
					class="relative bg-gray-800 border-2 border-gray-100"
					bind:this={polaroidElements[polaroid.id]}
				>
					<img src={polaroid.src} alt="A polaroid" class="w-full h-auto aspect-square object-cover" />
					{#if polaroid.stickers}
						{#each polaroid.stickers as sticker (sticker.id)}
							<DraggableSticker
								{sticker}
								editing={polaroid.editing}
								polaroidElement={polaroidElements[polaroid.id]}
								on:update={(e) => handleStickerUpdate(e, polaroid.id)}
								on:dragend={() => saveChanges(polaroid)}
							/>
						{/each}
					{/if}
				</div>

				<div class="w-full text-center px-4 h-20">
					{#if polaroid.editing}
						<textarea
							bind:value={polaroid.description}
							placeholder="Add a description..."
							class="text-center w-full border-gray-300 rounded-md shadow-sm focus:border-rose-300 focus:ring focus:ring-rose-200 focus:ring-opacity-50 text-sm p-1 resize-none bg-rose-200"
						></textarea>
						<input
							type="date"
							class="mt-1 w-full text-center border-gray-300 rounded-md shadow-sm focus:border-rose-300 focus:ring focus:ring-rose-200 focus:ring-opacity-50 text-xs p-1"
							value={formatDateForInput(polaroid.createdAt)}
							on:change={(e) => handleDateChange(e, polaroid.id)}
						/>
					{:else}
						<p class="text-center text-gray-700 font-serif italic text-sm line-clamp-3 wrap-break-word h-15">
							{polaroid.description || ''}
						</p>
						<div class="text-center text-gray-500 text-xs mt-2">
							{polaroid.createdAt.toLocaleDateString('en-US', {
								year: 'numeric',
								month: 'long',
								day: 'numeric'
							})}
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
