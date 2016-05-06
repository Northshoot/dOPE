

def stats_string(total_inserts, repeat_inserts, rebal_events, evict_events,
                 flush_events, MtoG, GtoC, miss_count,
                 sync_count, rebal_count, ciphers_sent, ciphers_received,
                 avg_msg_size, n_miss_inserts, g_rts, c_rts):
    '''
    Return a formatted string of dOPE/mOPE statistics to report
    simulation results
    '''
    ret = "-----------------------------Data Inserted-----------------------------\n"
    ret += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    ret += "***Total inserts = " + total_inserts +"***\n"
    ret += "***Total repeated syncs " + repeat_inserts + "***\n\n"
    ret += "------------------------------Event Count-----------------------------\n"
    ret += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    ret += "***Tree rebalances = " + rebal_events + "***\n"
    ret += "***Sensor evictions = " + evict_events + "***\n"
    ret += "***Sensor flushes for rebalance = " + flush_events + "***\n\n"
    ret += "-----------------------------Message Count----------------------------\n"
    ret += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    ret += "|Embedded to Gateway | Gateway to Cloud|\n"
    ret += "|--------------------|-----------------|\n"
    ret += "|      " +MtoG+ "        |     " + GtoC +"       |\n"
    ret += "----------------------------------------\n"
    ret += "|   Misses  |   Syncs   |  Rebalances   |\n"
    ret += "|-----------|-----------|---------------|\n" 
    ret += "|   " + miss_count + "    |      " + sync_count + "   |     " + rebal_count + "       |\n\n"
    ret += "----------------Ciphertexts sent, proxy for bytes sent----------------\n"
    ret += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    ret += "| Number of ciphertexts sent by the sensor: " + ciphers_sent + "\n"
    ret += "| Number of ciphertexts sent back to the sensor: " + ciphers_received + "\n"
    ret += "| Average ciphertexts per message sent back to sensor: " + avg_msg_size+ "\n\n" 
    ret += "-------------------------Round Trip Breakdown-----------------------\n"
    ret += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    ret += "Number of inserts requiring traversal: " + n_miss_inserts +"\n"
    ret += "| Average RTs to gateway  | Average RTs to cloud  |\n"
    ret += "--------------------------------------------------------\n"
    ret += "|           " + g_rts + "           |   " + c_rts + "    |\n"

    return ret
