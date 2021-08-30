
# Writmacs

This is a Python library for producing documents with special formatting in HTML, Markdown, and plain text.

## Target formats

<dl>
<dt>HTML (<code>&quot;html&quot;</code>)</dt>

<dd>accessible, semantic, featureful</dd>

<dt>Markdown (<code>&quot;md&quot;</code>)</dt>

<dd>hacky, mainly for instant messaging</dd>

<dt>Text (<code>&quot;txt&quot;</code>)</dt>

<dd>very hacky, for oppressive evironments that don't give you any other options</dd>
</dl>

## Syntax

Text is marked up with syntax similar to LaTeX:

```
I used %em{emphasis} in this sentence.
```

Parens may be curly braces, square brackets, parentheses, quotes, and backticks. They may be duplicated to avoid conflicting with characters inside.

```
%mono{ %smallcaps( %studly{{{
  You can have "{{}}" in here without breaking anything.

  It takes three "}"s to close this tag.
}}})}
```

## Transformations

| Macro       | Tag Names        | Text Result                | Markdown Result                    | HTML Result                                                                |
|:------------|:-----------------|:---------------------------|:-----------------------------------|:---------------------------------------------------------------------------|
| Emphasized  | em, emphasize    | <code>𝘦𝘹𝘢𝘮𝘱𝘭𝘦</code>       | <code>&ast;example&ast;</code>     | <code>&lt;em&gt;example&lt;/em&gt;</code>                                  |
| Monospaced  | mono, monospace  | <code>𝚎𝚡𝚊𝚖𝚙𝚕𝚎</code>       | <code>&grave;example&grave;</code> | <code>&lt;code&gt;example&lt;/code&gt;</code>                              |
| Rotated     | rot, rotate      | <code>ǝ˥dɯɐxǝ</code>       | <code>ǝ˥dɯɐxǝ</code>               | <code>ǝ˥dɯɐxǝ</code>                                                       |
| Small Caps  | smallcaps        | <code>ᴇxᴀᴍᴘʟᴇ</code>       | <code>ᴇxᴀᴍᴘʟᴇ</code>               | <code>&lt;span class=&quot;small-caps&quot;&gt;example&lt;/span&gt;</code> |
| Sparkly     | sparkle, sparkly | <code>✧⭒͙°example✧ﾟ☆</code> | <code>✧⭒͙°example✧ﾟ☆</code>         | <code>✧⭒͙°example✧ﾟ☆</code>                                                 |
| Studly      | studly           | <code>eXaMPLE</code>       | <code>ExAmpLE</code>               | <code>exAmpLe</code>                                                       |
| Underlined  | under, underline | <code>e̠x̠a̠m̠pl̠e̠</code>       | <code>e̠x̠a̠m̠pl̠e̠</code>               | <code>&lt;span class=&quot;underlined&quot;&gt;example&lt;/span&gt;</code> |


## To-Do

- more transformations
  - zalgo (WIP)
  - superscript (WIP)
  - snippets (WIP)
  - wide
  - subscript
- pop-up window for quick text insertion
- command line access to individual transformation functions
