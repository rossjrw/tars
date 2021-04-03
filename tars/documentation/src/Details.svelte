<script>
  export let argument

  const nargs = {
    null: 1,
    0: "0",
    "+": "at least 1",
    "*": "any",
    "?": "either 0 or 1",
  }

  const typeNargs = {
    bool: "0",
    longstr: "1",
  }

  const types = {
    str: "string",
    longstr: "a long string that may contain spaces",
    int: "number",
    bool: "boolean",
    regex_type: "regular expression",
  }

  const details = [
    [
      "number of values",
      typeNargs[argument.type] || nargs[argument.nargs] || argument.nargs
    ],
    ["value type", types[argument.type] || argument.type],
    [
      "choices for value",
      argument.choices
        ? new Intl.ListFormat("en", { type: "disjunction" }).format(
          argument.choices.map(choice => `<code>${choice}</code>`)
        )
        : false
    ],
    ["default value", argument.default],
    [
      "permission level",
      argument.permission ? "🔒 requires elevated permissions" : false
    ],
  ].filter(([_, info]) => Boolean(info))
</script>

<table class="block mb-4">
  <tbody class="divide-y-2 divide-primary-dark divide-dashed
                bg-primary-dark bg-opacity-40 rounded">
    {#each details as [item, info]}
      <tr class="divide-dashed divide-primary-dark divide-x-2">
        <td class="px-2 py-1 text-primary-lighter font-bold">{item}</td>
        <td class="px-2 py-1">{@html info}</td>
      </tr>
    {/each}
  </tbody>
</table>
