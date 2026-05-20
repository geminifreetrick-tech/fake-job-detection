/**
 * Tiny, safe-ish markdown renderer for short awareness articles.
 * Supports: headings (#, ##, ###), bold (**), italic (*), inline code (`),
 * unordered lists (-), blockquotes (>), paragraphs.
 *
 * We deliberately don't accept raw HTML — text is escaped.
 */
import React from 'react'

function escape(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c] as string))
}

function renderInline(line: string): React.ReactNode {
  // Escape first, then re-introduce structural spans.
  let html = escape(line)
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-100 px-1 py-0.5 rounded">$1</code>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  return <span dangerouslySetInnerHTML={{ __html: html }} />
}

export function Markdown({ source }: { source: string }) {
  const lines = source.replace(/\r\n/g, '\n').split('\n')
  const out: React.ReactNode[] = []
  let para: string[] = []
  let listBuf: string[] = []

  function flushPara() {
    if (para.length) {
      out.push(
        <p key={`p-${out.length}`} className="mb-3 leading-7">
          {renderInline(para.join(' '))}
        </p>,
      )
      para = []
    }
  }
  function flushList() {
    if (listBuf.length) {
      out.push(
        <ul key={`u-${out.length}`} className="list-disc list-inside mb-3 space-y-1">
          {listBuf.map((item, i) => (
            <li key={i}>{renderInline(item.replace(/^[-*]\s+/, ''))}</li>
          ))}
        </ul>,
      )
      listBuf = []
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line.trim()) {
      flushPara()
      flushList()
      continue
    }
    if (/^### /.test(line)) {
      flushPara(); flushList()
      out.push(
        <h3 key={`h-${out.length}`} className="text-lg font-semibold mt-4 mb-2">
          {renderInline(line.slice(4))}
        </h3>,
      )
      continue
    }
    if (/^## /.test(line)) {
      flushPara(); flushList()
      out.push(
        <h2 key={`h-${out.length}`} className="text-xl font-semibold mt-5 mb-2">
          {renderInline(line.slice(3))}
        </h2>,
      )
      continue
    }
    if (/^# /.test(line)) {
      flushPara(); flushList()
      out.push(
        <h1 key={`h-${out.length}`} className="text-2xl font-bold mt-2 mb-3">
          {renderInline(line.slice(2))}
        </h1>,
      )
      continue
    }
    if (/^>\s+/.test(line)) {
      flushPara(); flushList()
      out.push(
        <blockquote key={`b-${out.length}`} className="border-l-4 border-brand-500 bg-brand-50 pl-3 py-2 my-3 italic text-slate-700">
          {renderInline(line.replace(/^>\s+/, ''))}
        </blockquote>,
      )
      continue
    }
    if (/^[-*]\s+/.test(line)) {
      flushPara()
      listBuf.push(line)
      continue
    }
    flushList()
    para.push(line)
  }
  flushPara(); flushList()
  return <div className="prose-sm max-w-none">{out}</div>
}
