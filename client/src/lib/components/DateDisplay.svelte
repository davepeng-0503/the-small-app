<script lang="ts">
  export let date: Date;
  export let location: string;
  export let locale: string = "en-AU";

  const day = new Intl.DateTimeFormat(locale, { weekday: "long" }).format(date);
  const dayNum = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const year = date.getFullYear();
  const formattedDate = `${dayNum}/${month}/${year}`;
</script>

<span
  class="inline-flex items-center rounded-2xl px-4 py-2 
  bg-linear-to-r from-rose-400/80 via-rose-500/70 to-rose-400/80 
  text-rose-50 font-semibold shadow-md backdrop-blur-sm
  hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
>
  <span class="italic text-rose-100">{day}</span>
  <span class="opacity-70 mx-1.5">•</span>
  <span class="italic text-rose-100">{formattedDate}</span>
  <span class="opacity-70 mx-1.5">•</span>
  <span class="italic text-rose-100">{location}</span>
</span>
