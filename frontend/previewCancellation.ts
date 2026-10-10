import type { ClientRequest, IncomingMessage, ServerResponse } from 'node:http'

type ProxyEvents = { on(event: 'proxyReq', listener: (outgoing: ClientRequest, incoming: IncomingMessage, response: ServerResponse) => void): unknown }

// Vite must forward RESPONSE disconnects after the POST body has been read.
// The IncomingMessage 'aborted' event alone does not cover this common case.
export function attachPreviewCancellation(proxy: ProxyEvents) {
  proxy.on('proxyReq', (outgoing, incoming, response) => {
    if (incoming.url?.split('?')[0] !== '/api/v1/meihua/traditional-preview') return
    const cancel = () => { if (!response.writableFinished) outgoing.destroy() }
    response.once('close', cancel)
    outgoing.once('close', () => response.off('close', cancel))
  })
}
