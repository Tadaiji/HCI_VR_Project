using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class targetColliderTriggerScript : MonoBehaviour
{
    [SerializeField]
    private GameObject player;

    public bool triggered = false;
    
    private void Start()
    {
        if (player == null)
            player = GameObject.FindGameObjectWithTag("Player");
    }

    private void OnTriggerEnter(Collider other)
    {
        triggered = true;
        print("headset collision");
        player.GetComponent<Controll>().Collision(other);
    }
}
