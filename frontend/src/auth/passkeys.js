function base64urlToBuffer(value) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const bytes = Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));
  return bytes.buffer;
}

function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let value = "";
  bytes.forEach((byte) => { value += String.fromCharCode(byte); });
  return btoa(value).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function creationOptions(options) {
  return {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    user: { ...options.user, id: base64urlToBuffer(options.user.id) },
    excludeCredentials: (options.excludeCredentials || []).map((credential) => ({
      ...credential,
      id: base64urlToBuffer(credential.id),
    })),
  };
}

function requestOptions(options) {
  return {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    allowCredentials: (options.allowCredentials || []).map((credential) => ({
      ...credential,
      id: base64urlToBuffer(credential.id),
    })),
  };
}

function registrationCredential(credential) {
  return {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment,
    clientExtensionResults: credential.getClientExtensionResults(),
    response: {
      attestationObject: bufferToBase64url(credential.response.attestationObject),
      clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
      transports: credential.response.getTransports?.() || ["internal"],
    },
  };
}

function authenticationCredential(credential) {
  return {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment,
    clientExtensionResults: credential.getClientExtensionResults(),
    response: {
      authenticatorData: bufferToBase64url(credential.response.authenticatorData),
      clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
      signature: bufferToBase64url(credential.response.signature),
      userHandle: credential.response.userHandle
        ? bufferToBase64url(credential.response.userHandle)
        : null,
    },
  };
}

export async function platformAuthenticatorAvailable() {
  if (!window.PublicKeyCredential) return false;
  return PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable?.() || false;
}

export async function createPlatformPasskey(options) {
  const credential = await navigator.credentials.create({ publicKey: creationOptions(options) });
  if (!credential) throw new Error("No se creó la credencial biométrica");
  return registrationCredential(credential);
}

export async function getPlatformPasskey(options) {
  const credential = await navigator.credentials.get({ publicKey: requestOptions(options) });
  if (!credential) throw new Error("No se recibió la credencial biométrica");
  return authenticationCredential(credential);
}
