"""Stripe checkout endpoints and webhook."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from emergentintegrations.payments.stripe.checkout import (
    CheckoutStatusResponse,
    StripeCheckout,
)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from catalogues import AGENT_CATALOGUE, AGENT_PACKAGES
from config import db, logger
from email_service import send_email_bounded, send_purchase_email
from models import CheckoutRequest, PaymentTransaction


router = APIRouter()


@router.post("/checkout/session")
async def create_checkout_session(request: CheckoutRequest, http_request: Request):
    try:
        agent_id_lower = request.agent_id.lower()
        if agent_id_lower not in AGENT_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid agent ID")

        agent_info = AGENT_PACKAGES[agent_id_lower]
        amount = agent_info["price"]

        success_url = f"{request.origin_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{request.origin_url}/cancel"

        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")

        host_url = str(http_request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)

        import stripe
        stripe.api_key = stripe_api_key

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product': agent_info["stripe_product_id"],
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "agent_id": request.agent_id,
                "agent_name": agent_info["name"],
                "source": "web_checkout"
            }
        )

        session_response = SimpleNamespace(
            session_id=session.id,
            url=session.url
        )

        transaction = PaymentTransaction(
            session_id=session_response.session_id,
            agent_id=request.agent_id,
            amount=amount,
            currency="eur",
            payment_status="pending",
            metadata={
                "agent_name": agent_info["name"],
                "source": "web_checkout",
                "stripe_product_id": agent_info["stripe_product_id"]
            }
        )

        transaction_doc = transaction.model_dump()
        transaction_doc['created_at'] = transaction_doc['created_at'].isoformat()
        transaction_doc['updated_at'] = transaction_doc['updated_at'].isoformat()

        await db.payment_transactions.insert_one(transaction_doc)

        logger.info(f"Created checkout session for agent {request.agent_id}: {session_response.session_id}")

        return {"url": session_response.url, "session_id": session_response.session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    try:
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")

        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        status_response: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)

        if status_response.payment_status == "paid":
            existing_transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if existing_transaction and existing_transaction.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "payment_status": "paid",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                logger.info(f"Payment completed for session {session_id}")

        return {
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "amount_total": status_response.amount_total,
            "currency": status_response.currency,
            "metadata": status_response.metadata
        }

    except Exception as e:
        logger.error(f"Error checking checkout status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Receive Stripe webhook events. Validates signature and, on
    checkout.session.completed, sends the customer their personal access email."""
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")

        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")
        if not webhook_secret:
            raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

        import stripe
        stripe.api_key = stripe_api_key

        try:
            stripe.Webhook.construct_event(
                payload=body,
                sig_header=signature,
                secret=webhook_secret,
            )
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            logger.error(f"Stripe webhook parse error: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")

        event = json.loads(body.decode("utf-8"))

        # Idempotency: swallow replayed webhook events
        event_id = event.get("id")
        if event_id:
            dedup = await db.stripe_events.update_one(
                {"event_id": event_id},
                {"$setOnInsert": {
                    "event_id": event_id,
                    "type": event.get("type"),
                    "received_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
            if dedup.upserted_id is None:
                logger.info(f"Stripe webhook event {event_id} already processed, skipping.")
                return JSONResponse(content={"status": "duplicate", "event_id": event_id}, status_code=200)

        event_type = event.get("type")
        if event_type != "checkout.session.completed":
            return JSONResponse(content={"status": "ignored", "type": event_type}, status_code=200)

        session_obj = event["data"]["object"]
        session_id = session_obj.get("id")
        payment_status = session_obj.get("payment_status")

        session_metadata = dict(session_obj.get("metadata") or {})
        agent_id = (session_metadata.get("agent_id") or "").strip().lower()
        level = (session_metadata.get("level") or "full").strip().lower()
        if level not in ("demo", "full"):
            level = "full"

        if not agent_id:
            existing = await db.payment_transactions.find_one({"session_id": session_id})
            if existing:
                agent_id = (existing.get("agent_id") or "").strip().lower()
                meta = existing.get("metadata") or {}
                if not level or level == "full":
                    level = (meta.get("level") or level or "full").lower()

        customer_details = session_obj.get("customer_details") or {}
        customer_email = customer_details.get("email") if customer_details else None
        customer_name = (customer_details.get("name") if customer_details else None) or "Cliente"

        update_doc = {
            "session_id": session_id,
            "agent_id": agent_id,
            "amount": (session_obj.get("amount_total") or 0) / 100,
            "currency": session_obj.get("currency") or "eur",
            "payment_status": payment_status or "unknown",
            "customer_email": customer_email,
            "customer_name": customer_name,
            "metadata": {**session_metadata, "level": level},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": update_doc,
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            upsert=True,
        )

        if payment_status == "paid" and customer_email and agent_id:
            agent_info = AGENT_CATALOGUE.get(agent_id, {})
            agent_name = agent_info.get("name", agent_id.upper())

            email_sent = await send_email_bounded(
                send_purchase_email,
                customer_email=customer_email,
                customer_name=customer_name,
                agent_name=agent_name,
                agent_id=agent_id,
                level=level,
            )
            if email_sent:
                logger.info(f"Access email sent to {customer_email} for {agent_id} ({level})")
            else:
                logger.warning(f"Failed to send access email to {customer_email} for session {session_id}")
        else:
            logger.info(
                f"Webhook processed but no email sent. session={session_id} "
                f"paid={payment_status} agent={agent_id} email={customer_email}"
            )

        return JSONResponse(content={"status": "success"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
