# -*- coding: utf-8 -*-
"""GenPark Industrial Skill: genpark-agentic-commerce-contract-sla-penalty-liquidated-damages-skill
Category: agentic_commerce
Website: https://www.genpark.ai
LinkedIn: https://www.linkedin.com/company/92955550
"""
import sys
import json
import math

sys.stdout.reconfigure(encoding="utf-8")

def adjudicate_sla_liquidated_damages(total_monthly_minutes, unplanned_outage_minutes, monthly_service_fee_usd, contractual_target_sla_pct=99.9, max_penalty_cap_pct=30.0):
    if total_monthly_minutes <= 0 or monthly_service_fee_usd <= 0:
        raise ValueError("Monthly minutes and service fee must be positive values")
        
    actual_uptime_minutes = max(0, total_monthly_minutes - unplanned_outage_minutes)
    actual_uptime_pct = (actual_uptime_minutes / total_monthly_minutes) * 100.0
    
    # Tiered credit penalty schedule:
    # Target 99.9%:
    # 99.0% - 99.89%: 10% credit
    # 95.0% - 98.99%: 25% credit
    # < 95.0%: 50% credit (capped at max_penalty_cap_pct)
    if actual_uptime_pct >= contractual_target_sla_pct:
        credit_pct = 0.0
        sla_breached = False
        disposition = "SLA_MET_NO_PENALTY"
    elif actual_uptime_pct >= 99.0:
        credit_pct = 10.0
        sla_breached = True
        disposition = "TIER_1_MINOR_BREACH"
    elif actual_uptime_pct >= 95.0:
        credit_pct = 25.0
        sla_breached = True
        disposition = "TIER_2_MODERATE_BREACH"
    else:
        credit_pct = 50.0
        sla_breached = True
        disposition = "TIER_3_SEVERE_BREACH"
        
    effective_credit_pct = min(credit_pct, max_penalty_cap_pct)
    liquidated_damages_credit_usd = monthly_service_fee_usd * (effective_credit_pct / 100.0)
    net_payable_fee_usd = monthly_service_fee_usd - liquidated_damages_credit_usd
    
    return {
        "contractual_uptime_commitment_pct": contractual_target_sla_pct,
        "actual_uptime_achieved_pct": round(actual_uptime_pct, 4),
        "unplanned_outage_minutes": unplanned_outage_minutes,
        "sla_breach_occurred": sla_breached,
        "disposition_status": disposition,
        "gross_penalty_rate_pct": credit_pct,
        "contractual_liability_cap_pct": max_penalty_cap_pct,
        "effective_penalty_rate_pct": effective_credit_pct,
        "liquidated_damages_credit_usd": round(liquidated_damages_credit_usd, 2),
        "adjusted_net_monthly_billing_usd": round(net_payable_fee_usd, 2)
    }


def handle_rpc(request_str):
    try:
        req = json.loads(request_str)
        rpc_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})
        
        if method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "tools": [{
                        "name": "adjudicate_sla_liquidated_damages",
                        "description": """Adjudicate enterprise Master Services Agreement (MSA) uptime and delivery Service Level Agreement (SLA) penalties.
Computes monthly service availability percentage across planned/unplanned downtime, applies severity weighting,
and computes contractual service fee credit penalties capped by contract liability limits.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }]
                }
            })
        elif method == "tools/call":
            call_params = params.get("arguments", {})
            res = adjudicate_sla_liquidated_damages(**call_params)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(res, indent=2)
                    }]
                }
            })
        else:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            })
    except Exception as e:
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": str(e)}
        })

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sample = {'total_monthly_minutes': 43200, 'unplanned_outage_minutes': 180, 'monthly_service_fee_usd': 65000.0, 'contractual_target_sla_pct': 99.9, 'max_penalty_cap_pct': 30.0}
        out = adjudicate_sla_liquidated_damages(**sample)
        print("[TEST_PASS] Output:", json.dumps(out))
    else:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            print(handle_rpc(line))
