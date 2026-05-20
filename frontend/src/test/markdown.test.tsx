import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import { Markdown } from '../lib/markdown'

describe('Markdown', () => {
  it('renders headings, bold, code, lists, and quotes', () => {
    const src = `# Title\n\nSome **bold** and \`code\` text.\n\n- one\n- two\n\n> quoted`
    const { container } = render(<Markdown source={src} />)
    expect(container.querySelector('h1')?.textContent).toBe('Title')
    expect(container.querySelector('strong')?.textContent).toBe('bold')
    expect(container.querySelector('code')?.textContent).toBe('code')
    expect(container.querySelectorAll('li')).toHaveLength(2)
    expect(container.querySelector('blockquote')?.textContent).toContain('quoted')
  })

  it('escapes raw HTML', () => {
    const { container } = render(<Markdown source={'<script>alert(1)</script>'} />)
    expect(container.querySelector('script')).toBeNull()
    expect(container.textContent).toContain('<script>')
  })
})
